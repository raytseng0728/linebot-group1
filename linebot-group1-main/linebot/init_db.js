const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./vocabulary.db');

db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  db.run(`CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    meaning TEXT,
    difficulty INTEGER DEFAULT 1
  )`);

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
  )`);

  console.log('資料表建立完成');
});

db.close();
