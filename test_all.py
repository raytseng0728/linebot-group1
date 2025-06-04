import register
import review
import learn
import quiz
import progress

def main():
    user_id = "test_user_123"
    display_name = "測試用戶"

    print("=== 測試用戶註冊 ===")
    result = register.register_user(user_id, display_name)
    print(result)

    print("\n=== 測試複習下一個單字 ===")
    word = review.get_next_review_word(user_id)
    print(word if word else "沒有需要複習的單字")

    print("\n=== 測試加入新單字學習 ===")
    learn_result = learn.add_new_word(user_id)
    print(learn_result)

    print("\n=== 測試隨機抽測驗單字 ===")
    quiz_word = quiz.get_quiz_word(user_id)
    print(quiz_word if quiz_word else "沒有可用來測驗的單字")

    print("\n=== 測試完成率 ===")
    percent = progress.get_progress_percentage(user_id)
    print(f"完成率: {percent}%")

if __name__ == "__main__":
    main()
