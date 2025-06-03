# register.py
import sqlite3

def register_user(user_id, display_name, cursor, conn):
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, display_name)
        VALUES (?, ?)
    """, (user_id, display_name))
    conn.commit()
    return f"歡迎你，{display_name}！你已成功註冊。"
