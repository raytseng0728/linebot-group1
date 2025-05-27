const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// 設定資料庫路徑
const dbPath = path.join(__dirname, 'vocabulary.db');
const db = new sqlite3.Database(dbPath);

console.log('🔧 正在初始化資料庫：', dbPath);

db.serialize(() => {
  // 使用者表格
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`, (err) => {
    if (err) console.error('❌ 建立 users 表格失敗:', err.message);
    else console.log('✅ users 表格建立完成');
  });

  // 單字表格
  db.run(`CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT,
    difficulty INTEGER DEFAULT 1
  )`, (err) => {
    if (err) console.error('❌ 建立 vocabulary 表格失敗:', err.message);
    else console.log('✅ vocabulary 表格建立完成');
  });

  // 學習進度表格
  db.run(`CREATE TABLE IF NOT EXISTS learning_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    word_id INTEGER NOT NULL,
    next_review DATETIME,
    ease_factor REAL DEFAULT 2.5,
    interval INTEGER DEFAULT 1,
    repetition INTEGER DEFAULT 0,
    last_review DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(word_id) REFERENCES vocabulary(id),
    UNIQUE(user_id, word_id)
  )`, (err) => {
    if (err) console.error('❌ 建立 learning_status 表格失敗:', err.message);
    else console.log('✅ learning_status 表格建立完成');
  });
});

db.close(() => {
  console.log('✅ 資料庫初始化結束並關閉連線');
});
