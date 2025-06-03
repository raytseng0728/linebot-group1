import sqlite3
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage, PostbackEvent

class LearnDB:
    def __init__(self, db_path="vocabulary.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def get_today_learned_count(self, user_id):
        self.cursor.execute("""
            SELECT COUNT(*) FROM learning_status
            WHERE user_id = ? AND DATE(last_review) = DATE('now')
        """, (user_id,))
        return self.cursor.fetchone()[0]

    def add_new_words_to_learning(self, user_id, limit=10):
        learned_today = self.get_today_learned_count(user_id)
        if learned_today >= limit:
            return []

        available_limit = limit - learned_today

        self.cursor.execute("""
            SELECT id, word, meaning, part_of_speech FROM vocabulary
            WHERE id NOT IN (
                SELECT word_id FROM learning_status WHERE user_id = ?
            )
            ORDER BY id ASC
            LIMIT ?
        """, (user_id, available_limit))
        new_words = self.cursor.fetchall()

        if new_words:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for word in new_words:
                word_id = word[0]
                self.cursor.execute("""
                    INSERT OR IGNORE INTO learning_status
                    (user_id, word_id, next_review, last_review, ease_factor, interval, repetition)
                    VALUES (?, ?, ?, ?, 2.5, 1, 0)
                """, (user_id, word_id, now, now))
            self.conn.commit()

        return new_words

    def close(self):
        self.conn.close()

def handle_postback(event: PostbackEvent, line_bot_api: LineBotApi, db: LearnDB):
    user_id = event.source.user_id
    data = event.postback.data

    if data == "action=learn":
        new_words = db.add_new_words_to_learning(user_id, limit=10)

        if new_words:
            reply_text = "🆕 加入以下新單字：\n\n"
            for word in new_words:
                word_text, meaning, part_of_speech = word[1], word[2], word[3] or "（無）"
                reply_text += f"📖 {word_text}\n詞性：{part_of_speech}\n意思：{meaning}\n\n"
        else:
            learned_today = db.get_today_learned_count(user_id)
            if learned_today >= 10:
                reply_text = "📚 你今天已經學過 10 個新單字囉！可以試著去複習看看 👀"
            else:
                reply_text = "🎉 你已學完所有單字！"

        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=reply_text)]
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text="❗️未定義的操作")]
        )
