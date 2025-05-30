from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import sqlite3
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = FastAPI()

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 確認環境變數是否成功讀取
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise RuntimeError("請先設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 資料庫初始化
db_path = "vocabulary.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT,
    difficulty INTEGER DEFAULT 1
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

        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)
        ''', (user_id, name))
        conn.commit()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"\u6b61\u8fce\u4f60\uff0c{name}\uff01\u4f60\u5df2\u6210\u529f\u8a3b\u518a\u3002")
        )

    elif user_message == "\u6211\u8981\u8907\u7fd2":
        cursor.execute('''
            SELECT v.word, v.meaning
            FROM learning_status ls
            JOIN vocabulary v ON ls.word_id = v.id
            WHERE ls.user_id = ?
            ORDER BY ls.next_review ASC
            LIMIT 1
        ''', (user_id,))
        word = cursor.fetchone()

        if word:
            reply = f"\u8907\u7fd2\u55ae\u5b57\uff1a{word[0]}\n\u610f\u601d\u662f\uff1a{word[1]}"
        else:
            reply = "\u76ee\u524d\u6c92\u6709\u9700\u8981\u8907\u7fd2\u7684\u55ae\u5b57\u3002"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "\u6211\u8981\u5b78\u7fd2":
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
            cursor.execute('''
                INSERT INTO learning_status (user_id, word_id)
                VALUES (?, ?)
            ''', (user_id, word_id))
            conn.commit()
            reply = f"\u65b0\u55ae\u5b57\uff1a{word}\n\u610f\u601d\u662f\uff1a{meaning}"
        else:
            reply = "\u4f60\u5df2\u5b78\u5b8c\u6240\u6709\u55ae\u5b57\uff01"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "\u6211\u8981\u6e2c\u9a57":
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
            reply = f"\u8acb\u554f\u300c{meaning}\u300d\u662f\u4ec0\u9ebc\u55ae\u5b57？"
        else:
            reply = "\u76ee\u524d\u6c92\u6709\u53ef\u4f9b\u6e2c\u9a57\u7684\u55ae\u5b57\u3002"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    elif user_message == "\u6211\u8981\u770b\u5b8c\u6210\u7387":
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM learning_status WHERE user_id = ?
        ''', (user_id,))
        learned = cursor.fetchone()[0]

        if total > 0:
            percent = round((learned / total) * 100, 1)
            reply = f"\u4f60\u5df2\u5b8c\u6210 {learned}/{total} 個單字，完成率 {percent}%"
        else:
            reply = "\u76ee\u524d\u55ae\u5b57\u5eab\u662f\u7a7a\u7684。"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="\u8acb輸入 /start 註冊或使用選單功能")
        )
