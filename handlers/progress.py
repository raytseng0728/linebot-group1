import sqlite3

def get_learning_progress(user_id, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM learning_status WHERE user_id = ?", (user_id,))
    learned = cursor.fetchone()[0]

    conn.close()

    if total == 0:
        return 0.0, learned, total
    percent = round((learned / total) * 100, 1)
    return percent, learned, total

if __name__ == "__main__":
    user_id = input("請輸入 user_id: ")
    percent, learned, total = get_learning_progress(user_id)
    print(f"完成率：{percent}% （{learned}/{total}）")
