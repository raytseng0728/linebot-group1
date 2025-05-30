import sqlite3

def get_random_quiz_word(user_id, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.word, v.meaning
        FROM vocabulary v
        JOIN learning_status ls ON v.id = ls.word_id
        WHERE ls.user_id = ?
        ORDER BY RANDOM()
        LIMIT 1
    """, (user_id,))
    quiz_word = cursor.fetchone()
    conn.close()
    return quiz_word

if __name__ == "__main__":
    user_id = input("請輸入 user_id: ")
    quiz = get_random_quiz_word(user_id)
    if quiz:
        print(f"請問「{quiz[1]}」是什麼單字？")
        print(f"答案是：{quiz[0]}")
    else:
        print("目前沒有已學過的單字可用於測驗。")
