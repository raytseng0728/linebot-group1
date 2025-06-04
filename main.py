from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, PostbackEvent, TextSendMessage,
    BubbleContainer, BoxComponent, ButtonComponent, FlexSendMessage,
    PostbackAction, TextComponent, FollowEvent
)
from linebot.exceptions import LineBotApiError, InvalidSignatureError
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import urllib.parse
from n import send_flex_menu
from review import (
    get_review_words_by_date,
    generate_review_calendar_picker,
    generate_review_day_picker
)
from learn import LearnDB, handle_postback as handle_learn_postback
from quiz import send_quiz_question
import matplotlib.pyplot as plt
from linebot.models import ImageSendMessage
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
import io
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise RuntimeError("請先設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()
conn = sqlite3.connect("vocabulary.db", check_same_thread=False)

def get_cursor():
    return conn.cursor()

def get_user_profile(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except LineBotApiError as e:
        print(f"取得使用者資訊錯誤: {e}")
        return "使用者"

@app.get("/progress_chart/{user_id}")
def progress_chart(user_id: str):
    cursor = get_cursor()

    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM learning_status WHERE user_id = ?", (user_id,))
    learned = cursor.fetchone()[0]

    if total == 0:
        percent = 0.0
    else:
        percent = round((learned / total) * 100, 1)

    labels = ['已學習', '未學習']
    sizes = [learned, total - learned]
    explode = (0.05, 0)
    colors = ['#4CAF50', '#EEEEEE']

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
           shadow=False, startangle=90, colors=colors, textprops={'fontsize': 12})
    ax.axis('equal')
    plt.title(f"單字完成率：{percent}% （{learned}/{total}）", fontsize=14)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return Response(buf.getvalue(), media_type="image/png")

def get_review_words(user_id, limit=10):
    cursor = get_cursor()
    cursor.execute('''
        SELECT v.word, v.meaning, v.part_of_speech
        FROM learning_status ls
        JOIN vocabulary v ON ls.word_id = v.id
        WHERE ls.user_id = ? AND (ls.next_review IS NULL OR ls.next_review <= datetime('now'))
        ORDER BY ls.next_review ASC
        LIMIT ?
    ''', (user_id, limit))
    return cursor.fetchall()

def update_review(user_id, word_id, quality):
    cursor = get_cursor()
    cursor.execute('''
        SELECT ease_factor, interval, repetition
        FROM learning_status
        WHERE user_id = ? AND word_id = ?
    ''', (user_id, word_id))
    row = cursor.fetchone()

    if row is None:
        ease_factor = 2.5
        interval = 1
        repetition = 0
    else:
        ease_factor, interval, repetition = row

    if quality < 3:
        repetition = 0
        interval = 1
    else:
        if repetition == 0:
            interval = 1
        elif repetition == 1:
            interval = 6
        else:
            interval = int(interval * ease_factor)
        repetition += 1

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(ease_factor, 1.3)

    next_review = datetime.now() + timedelta(days=interval)
    next_review_str = next_review.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO learning_status (user_id, word_id, ease_factor, interval, repetition, next_review, last_review)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, word_id) DO UPDATE SET
            ease_factor=excluded.ease_factor,
            interval=excluded.interval,
            repetition=excluded.repetition,
            next_review=excluded.next_review,
            last_review=datetime('now')
    ''', (user_id, word_id, ease_factor, interval, repetition, next_review_str))
    conn.commit()

@app.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode("utf-8")
    print("Received webhook:", body_str)

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except LineBotApiError as e:
        print(f"LINE API Error: {e}")
        raise HTTPException(status_code=500, detail="LINE API error")

    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    name = get_user_profile(user_id)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(
        text=f"👋 嗨 {name}，歡迎加入單字機器人！請先輸入 /start 開始使用 ✨"
    ))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    cursor = get_cursor()

    if user_message == "/start":
        cursor.execute("SELECT display_name FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            name = get_user_profile(user_id)
            cursor.execute("INSERT INTO users (user_id, display_name) VALUES (?, ?)", (user_id, name))
            conn.commit()
            welcome_text = f"👋 歡迎你，{name}！你已成功註冊。"
        else:
            name = row[0]
            welcome_text = f"👋 歡迎回來，{name}！請使用下方選單繼續你的學習旅程。"
        messages = [TextSendMessage(text=welcome_text), send_flex_menu()]
        line_bot_api.reply_message(event.reply_token, messages=messages)
        return

    if user_message == "選單":
         line_bot_api.reply_message(event.reply_token, send_flex_menu(user_id))
         return

    if user_message in ["/help", "說明"]:
        instruction_text = """這是一個幫助你學習單字的 LINE 機器人 ✨
你可以使用下方的選單開始操作，或輸入以下指令：

🔹 開始學習：註冊帳號並初始化學習
🔹 單字庫複習中：複習你已經學過的單字
🔹 新單字學習：從未看過的新單字
🔹 單字小考中：隨機測驗單字
🔹 完成率：查看目前進度
🔹 結束：結束今天的學習

📌 指令提示：
👉 /start 註冊帳號
👉 /unbind 解除選單
👉 輸入「小考」、「複習」、「學習」也能快速觸發對應功能！

祝你學習順利，加油 💪"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=instruction_text))
        return

    if user_message == "/unbind":
        try:
            line_bot_api.unlink_rich_menu_from_user(user_id)
            reply_text = "✅ 已成功解除你手機上的 Rich Menu 綁定！"
        except LineBotApiError as e:
            print(f"解除綁定失敗: {e}")
            reply_text = "❌ 解除 Rich Menu 綁定時發生錯誤，請稍後再試。"
        messages = [TextSendMessage(text=reply_text), send_flex_menu()]
        line_bot_api.reply_message(event.reply_token, messages=messages)
        return

    if user_message == "今天":
        words = get_review_words(user_id)
        if words:
            word_text = "\n\n".join([f"📖 {w}\n意思：{m}" for w, m, _ in words[:10]])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=word_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="今天沒有該複習的單字喔！"))
        return

    if user_message == "以前":
        line_bot_api.reply_message(event.reply_token, generate_review_calendar_picker())
        return

    if user_message in ["我要複習", "複習"]:
        line_bot_api.reply_message(event.reply_token, generate_review_day_picker())
        return

    if user_message in ["小考", "單字小考"]:
        message = send_quiz_question(user_id)
        line_bot_api.reply_message(event.reply_token, message)
        return

    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="👋 歡迎使用單字機器人！請先輸入 /start 完成註冊，才能開始使用功能喔！"
        ))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="抱歉，我不太懂你的指令，可以試試看選單操作喔！"
        ))
    if user_message == "完成率":
        image_url = f"https://1b3e-163-14-216-131.ngrok-free.app/progress_chart/{user_id}"
        image_message = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
        line_bot_api.reply_message(event.reply_token, send_flex_menu(user_id))
        return

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data
    params = dict(urllib.parse.parse_qsl(data))
    action = params.get("action")

    if action == "quiz":
        message = send_quiz_question(event.reply_token, user_id)
        line_bot_api.reply_message(event.reply_token, message)

    elif action == "quiz_answer":
        user_answer = params.get("answer")
        correct_answer = params.get("correct")
        word_id = int(params.get("word_id"))

        cursor = get_cursor()
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            '''SELECT quiz_count FROM quiz_limit WHERE user_id = ? AND quiz_date = ?''',
            (user_id, today_str)
        )
        row = cursor.fetchone()

        is_correct = 1 if user_answer == correct_answer else 0
        cursor.execute(
            '''INSERT INTO quiz_log (user_id, word_id, answer, correct_answer, is_correct, answer_time)
               VALUES (?, ?, ?, ?, ?, datetime('now'))''',
            (user_id, word_id, user_answer, correct_answer, is_correct)
        )

        if row:
            cursor.execute(
                '''UPDATE quiz_limit SET quiz_count = quiz_count + 1 WHERE user_id = ? AND quiz_date = ?''',
                (user_id, today_str)
            )
        else:
            cursor.execute(
                '''INSERT INTO quiz_limit (user_id, quiz_date, quiz_count) VALUES (?, ?, 1)''',
                (user_id, today_str)
            )

        conn.commit()

        cursor.execute(
            '''SELECT COUNT(*) FROM quiz_log 
               WHERE user_id = ? AND date(answer_time) = date('now') AND is_correct = 1''',
            (user_id,)
        )
        correct_today = cursor.fetchone()[0]

        result_text = "✅ 恭喜你答對了！" if is_correct else f"❌ 答錯了，正確答案是：{correct_answer}"
        result_text += f"\n🎯 今日答對題數：{correct_today}/10"

        confirm_bubble = BubbleContainer(
            direction="ltr",
            body=BoxComponent(
                layout="vertical",
                contents=[
                    TextComponent(text=result_text, weight="bold", wrap=True),
                    TextComponent(text="還要繼續挑戰下一題嗎？", margin="md"),
                    BoxComponent(
                        layout="horizontal",
                        spacing="sm",
                        contents=[
                            ButtonComponent(
                                style="primary",
                                height="sm",
                                action=PostbackAction(label="✅ 繼續", data="action=quiz")
                            ),
                            ButtonComponent(
                                style="secondary",
                                height="sm",
                                action=PostbackAction(label="❌ 結束", data="action=quit_quiz")
                            )
                        ],
                        margin="md"
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="答題結果", contents=confirm_bubble))

    elif action == "quit_quiz":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📘 小考結束，歡迎隨時再來挑戰！"))

    elif action == "review":
        line_bot_api.reply_message(event.reply_token, generate_review_day_picker())

    elif action == "review_by_date":
        review_date = params.get("date")
        words = get_review_words_by_date(user_id, review_date)
        if words:
            word_text = "\n\n".join([
                f"📖 {row[0]}\n詞性：{row[2] or '（無）'}\n意思：{row[1]}"
                for row in words[:10]
            ])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=word_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 那天沒有複習過的單字喔！"))

    elif action == "review_today":
        words = get_review_words(user_id)
        if words:
            word_text = "\n\n".join([
                f"📖 {row[0]}\n詞性：{row[2] or '（無）'}\n意思：{row[1]}"
                for row in words[:10]
            ])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=word_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="今天沒有該複習的單字喔！"))

    elif action == "review_calendar":
        line_bot_api.reply_message(event.reply_token, generate_review_calendar_picker())

    elif action == "start":
        event.message = TextMessage(text="/start")
        handle_message(event)

    elif action == "learn":
        db = LearnDB()
        handle_learn_postback(event, line_bot_api, db)
        db.close()

    elif action == "progress":
        user_id = event.source.user_id

        # 計算完成率
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_status WHERE user_id = ?", (user_id,))
        learned = cursor.fetchone()[0]

        if total == 0:
            percent = 0.0
        else:
            percent = round((learned / total) * 100, 1)

        # 建立圖片網址（記得替換 ngrok 網址）
        pie_url = f"https://1b71-163-14-216-131.ngrok-free.app/progress_chart/{user_id}"

        # 傳送圖片 + 文字
        messages = [
            ImageSendMessage(original_content_url=pie_url, preview_image_url=pie_url),
            TextSendMessage(text=f"🎯 你已完成 {percent}% 的單字學習（{learned}/{total}）")
        ]
        line_bot_api.reply_message(event.reply_token, messages)


    elif action == "help":
        event.message = TextMessage(text="/help")
        handle_message(event)

    elif action == "settings":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚙️ 設定功能尚未實作，敬請期待！"))

    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="功能尚未實作，敬請期待！"))
