ffrom fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise RuntimeError("請先設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()

# 建立連線與 cursor，check_same_thread=False 允許多線程使用
conn = sqlite3.connect("vocabulary.db", check_same_thread=False)
cursor = conn.cursor()

# 建表（如果還沒建立）
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS learning_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    word_id INTEGER NOT NULL,
    next_review DATETIME,
    ease_factor REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 1,
    repetition INTEGER DEFAULT 0,
    last_review DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(word_id) REFERENCES vocabulary(id),
    UNIQUE(user_id, word_id)
)
''')

conn.commit()

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@app.get("/check-users")
async def check_users():
    try:
        cursor.execute("SELECT user_id, display_name, created_at FROM users")
        rows = cursor.fetchall()
        users = [{"user_id": r[0], "display_name": r[1], "created_at": r[2]} for r in rows]
        return JSONResponse(content=users)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    if user_message == "/start":
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)",
            (user_id, name)
        )
        conn.commit()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"歡迎你，{name}！你已成功註冊。")
        )

    elif user_message == "我要複習":
        cursor.execute('''
            SELECT v.word, v.meaning
            FROM learning_status ls
            JOIN vocabulary v ON ls.word_id = v.id
            WHERE ls.user_id = ? AND (ls.next_review IS NULL OR ls.next_review <= datetime('now'))
            ORDER BY ls.next_review ASC
            LIMIT 1
        ''', (user_id,))
        word = cursor.fetchone()
        if word:
            reply = f"複習單字：{word[0]}\n意思是：{word[1]}"
        else:
            reply = "目前沒有需要複習的單字。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "我要學習":
        cursor.execute('''
            SELECT id, word, meaning FROM vocabulary
            WHERE id NOT IN (
                SELECT word_id FROM learning_status WHERE user_id = ?
            )
            LIMIT 1
        ''', (user_id,))
        new_word = cursor.fetchone()
        if new_word:
            word_id, word, meaning = new_word
            # 新增學習清單，next_review 設為現在時間
            cursor.execute('''
                INSERT INTO learning_status (user_id, word_id, next_review, last_review)
                VALUES (?, ?, datetime('now'), datetime('now'))
            ''', (user_id, word_id))
            conn.commit()
            reply = f"新單字：{word}\n意思是：{meaning}"
        else:
            reply = "你已學完所有單字！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "我要測驗":
        cursor.execute('''
            SELECT v.word, v.meaning
            FROM vocabulary v
            JOIN learning_status ls ON v.id = ls.word_id
            WHERE ls.user_id = ?
            ORDER BY RANDOM()
            LIMIT 1
        ''', (user_id,))
        quiz_word = cursor.fetchone()
        if quiz_word:
            word, meaning = quiz_word
            reply = f"請問「{meaning}」是什麼單字？"
        else:
            reply = "目前沒有可供測驗的單字。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "我要完成率":
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM learning_status WHERE user_id = ?", (user_id,))
        learned = cursor.fetchone()[0]
        if total > 0:
            percent = round((learned / total) * 100, 1)
            reply = f"你已完成 {learned}/{total} 個單字，完成率 {percent}%"
        else:
            reply = "目前單字庫是空的。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入 /start 註冊或使用選單功能")
        )
