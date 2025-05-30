import sqlite3
from datetime import datetime, timedelta

class LearnDB:
    def __init__(self, db_path="vocabulary.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def add_user(self, user_id, display_name):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)",
            (user_id, display_name)
        )
        self.conn.commit()

    def add_new_word_to_learning(self, user_id, word_id):
        # 新增一筆學習紀錄，初始next_review時間設為現在
        now = datetime.now()
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO learning_status 
            (user_id, word_id, next_review, ease_factor, interval, repetition, last_review)
            VALUES (?, ?, ?, 2.5, 1, 0, ?)
            """,
            (user_id, word_id, now, now)
        )
        self.conn.commit()

    def get_next_review_word(self, user_id):
        # 取出該用戶目前最早要複習的單字
        now = datetime.now()
        self.cursor.execute(
            """
            SELECT v.word, v.meaning, ls.next_review
            FROM learning_status ls
            JOIN vocabulary v ON ls.word_id = v.id
            WHERE ls.user_id = ? AND (ls.next_review IS NULL OR ls.next_review <= ?)
            ORDER BY ls.next_review ASC
            LIMIT 1
            """,
            (user_id, now)
        )
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
