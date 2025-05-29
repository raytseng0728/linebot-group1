const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'vocabulary.db');
console.log('🔍 目前使用的資料庫路徑：', dbPath);

const db = new sqlite3.Database(dbPath, sqlite3.OPEN_READONLY, (err) => {
  if (err) {
    console.error('❌ 無法開啟資料庫:', err.message);
    return;
  }
});

db.all('SELECT * FROM users', [], (err, rows) => {
  if (err) {
    console.error('❌ 讀取 users 表錯誤:', err.message);
  } else {
    console.log(`📄 users 表資料筆數：${rows.length}`);
    rows.forEach((row, i) => {
      console.log(`${i + 1}:`, row);
    });
  }
  db.close(() => {
    console.log('✅ 資料庫連線已關閉');
  });
});
