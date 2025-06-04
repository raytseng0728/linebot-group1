from flask import Flask, Response
import sqlite3
import matplotlib.pyplot as plt
import io
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # 微軟正黑體顯示中文
matplotlib.rcParams['axes.unicode_minus'] = False  # 正常顯示負號

app = Flask(__name__)

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

@app.route("/progress_chart/<user_id>")
def progress_chart(user_id):
    percent, learned, total = get_learning_progress(user_id)
    labels = ['已學習', '未學習']
    sizes = [learned, total - learned]
    explode = (0.05, 0)
    colors = ['#4CAF50', '#EEEEEE']

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
           shadow=False, startangle=90, colors=colors, textprops={'fontsize': 12})
    ax.axis('equal')
    plt.title(f"單字完成率：{percent}% （{learned}/{total}）", fontsize=14)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return Response(buf.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    app.run(port=8000, debug=True)
