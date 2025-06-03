import sqlite3
from datetime import datetime, date, timedelta
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    ButtonComponent, TextComponent, PostbackAction
)

def get_review_words_by_date(user_id, review_date=None, db_path="vocabulary.db"):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        if review_date is None:
            review_date = date.today().isoformat()

        cursor.execute("""
            SELECT v.word, v.meaning, v.part_of_speech, DATE(ls.last_review)
            FROM learning_status ls
            JOIN vocabulary v ON ls.word_id = v.id
            WHERE ls.user_id = ? AND DATE(ls.last_review) = ?
            ORDER BY ls.last_review DESC
        """, (user_id, review_date))

        return cursor.fetchall()

def generate_review_calendar_picker():
    today = date.today()
    date_options = [(today - timedelta(days=i)).isoformat() for i in range(1, 13)]  # 昨天到前 12 天
    date_options.reverse()

    rows = []
    for i in range(0, len(date_options), 3):  # 每排 3 個
        row = BoxComponent(
            layout="horizontal",
            spacing="sm",
            contents=[
                ButtonComponent(
                    style="primary",
                    height="md",  # 按鈕變高變大
                    action=PostbackAction(
                        label=f"{datetime.strptime(d, '%Y-%m-%d').month}/{datetime.strptime(d, '%Y-%m-%d').day}",
                        data=f"action=review_by_date&date={d}"
                    )
                ) for d in date_options[i:i+3]
            ]
        )
        rows.append(row)

    bubble = BubbleContainer(
        direction="ltr",
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text="📅 選擇複習日期", weight="bold", size="lg", wrap=True),
                *rows
            ],
            spacing="md"
        )
    )

    return FlexSendMessage(alt_text="請選擇複習日期", contents=bubble)

def generate_review_day_picker():
    bubble = BubbleContainer(
        direction="ltr",
        body=BoxComponent(
            layout="vertical",
            spacing="md",
            contents=[
                TextComponent(
                    text="📅 你想複習哪一天的單字？",
                    weight="bold",
                    size="lg",
                    wrap=True
                ),
                BoxComponent(
                    layout="horizontal",
                    spacing="sm",
                    contents=[
                        ButtonComponent(
                            style="primary",
                            height="sm",
                            action=PostbackAction(label="今天", data="action=review_today")
                        ),
                        ButtonComponent(
                            style="primary",
                            height="sm",
                            action=PostbackAction(label="以前", data="action=review_calendar")
                        )
                    ]
                )
            ]
        )
    )
    return FlexSendMessage(alt_text="請選擇複習時間", contents=bubble)

# CLI 測試模式（開發用）
if __name__ == "__main__":
    user_id = input("請輸入 user_id: ")
    mode = input("要查『今天』還是指定日期？（輸入 today 或 yyyy-mm-dd）：").strip()

    if mode.lower() == "today":
        words = get_review_words_by_date(user_id)
    else:
        words = get_review_words_by_date(user_id, mode)

    if words:
        print(f"🔁 查詢到 {len(words)} 筆單字：\n")
        for w, m, p, d in words:
            print(f"📖 單字：{w}\n詞性：{p}\n意思：{m}\n最近複習：{d}\n")
    else:
        print("❌ 沒有找到符合的單字。")
