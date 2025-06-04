from flask import Flask, Response 
import sqlite3
import matplotlib.pyplot as plt
import io
import matplotlib

app = Flask(__name__)

def get_learning_progress(user_id, db_path="vocabulary.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM learning_status WHERE user_id = ?", (user_id,))
    learned = cursor.fetchone()[0]
    conn.close()
    percent = round((learned / total) * 100, 1) if total else 0.0
    return percent, learned, total

@app.route("/progress_chart/<user_id>")
def progress_chart(user_id):
    percent, learned, total = get_learning_progress(user_id)
    labels = ['Learned', 'Not Learned']
    sizes = [learned, total - learned]
    colors = ['#4CAF50', '#EEEEEE']
    explode = (0.05, 0)

    fig, ax = plt.subplots()
    ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
           startangle=90, colors=colors, textprops={'fontsize': 12})
    ax.axis('equal')
    plt.title(f"Vocabulary Progress: {percent}% ({learned}/{total})", fontsize=14)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    app.run(port=8000, debug=True)
