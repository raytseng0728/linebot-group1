import sqlite3

def register_user(user_id, display_name, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, display_name)
        VALUES (?, ?)
    """, (user_id, display_name))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    user_id = input("請輸入 user_id: ")
    display_name = input("請輸入 display_name: ")
    register_user(user_id, display_name)
    print(f"用戶 {display_name} 已註冊。")
