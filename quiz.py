import sqlite3
import random
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction
)

def send_quiz_question(reply_token, user_id, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 抽 1 題單字（英文、詞性、正確中文意思）
    cursor.execute("""
        SELECT id, word, part_of_speech, meaning FROM vocabulary
        WHERE id IN (
            SELECT word_id FROM learning_status WHERE user_id = ?
        )
        ORDER BY RANDOM() LIMIT 1
    """, (user_id,))
    quiz = cursor.fetchone()

    if not quiz:
        conn.close()
        return FlexSendMessage(alt_text="沒有單字可測驗", contents=BubbleContainer(
            direction="ltr",
            body=BoxComponent(
                layout="vertical",
                contents=[TextComponent(text="⚠️ 目前沒有可用的單字進行小考！")]
            )
        ))

    word_id, word, pos, correct_meaning = quiz

    # 抽出 3 個不同錯誤中文意思（不能和正確的一樣）
    cursor.execute("""
        SELECT DISTINCT meaning FROM vocabulary
        WHERE meaning != ? AND id != ?
        ORDER BY RANDOM() LIMIT 3
    """, (correct_meaning, word_id))
    distractors = [row[0] for row in cursor.fetchall()]

    conn.close()

    # 混合正確答案與干擾選項
    all_options = distractors + [correct_meaning]
    random.shuffle(all_options)

    # 產生按鈕（只顯示意思）
    buttons = [
        ButtonComponent(
            style="primary",
            height="sm",
            action=PostbackAction(
                label=opt,
                data=f"action=quiz_answer&word_id={word_id}&answer={opt}&correct={correct_meaning}"
            )
        ) for opt in all_options
    ]

    pos_text = pos if pos else "無"

    bubble = BubbleContainer(
        direction="ltr",
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text=f"📖「{word}」 ({pos_text}) 是什麼意思？",
                    wrap=True,
                    weight="bold"
                ),
                *buttons
            ],
            spacing="md"
        )
    )

    return FlexSendMessage(alt_text="單字小考", contents=bubble)
