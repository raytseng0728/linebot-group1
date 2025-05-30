import sqlite3
from datetime import datetime

def get_next_review_word(user_id, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        SELECT v.word, v.meaning, ls.next_review
        FROM learning_status ls
        JOIN vocabulary v ON ls.word_id = v.id
        WHERE ls.user_id = ? AND (ls.next_review IS NULL OR ls.next_review <= ?)
        ORDER BY ls.next_review ASC
        LIMIT 1
    """, (user_id, now))
    word = cursor.fetchone()
    conn.close()
    return word

if __name__ == "__main__":
    user_id = input("請輸入 user_id: ")
    word = get_next_review_word(user_id)
    if word:
        print(f"複習單字：{word[0]}, 意思：{word[1]}, 預計複習時間：{word[2]}")
    else:
        print("目前沒有需要複習的單字。")
