const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 10000;

const config = {
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.LINE_CHANNEL_SECRET,
};

const client = new line.Client(config);

const dbPath = './vocabulary.db';
console.log('🔍 使用中的資料庫路徑：', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('❌ 無法連線到資料庫：', err.message);
  } else {
    console.log('✅ 已連線到資料庫');
    db.run(`CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      display_name TEXT,
      join_date TEXT DEFAULT (datetime('now'))
    )`);
  }
});

app.use(express.json());

app.post('/webhook', line.middleware(config), (req, res) => {
  console.log('📥 收到 webhook');
  Promise.all(req.body.events.map(handleEvent))
    .then(result => res.json(result))
    .catch(err => {
      console.error('❌ webhook 處理錯誤：', err);
      res.status(500).end();
    });
});

async function handleEvent(event) {
  if (event.type !== 'message' || event.message.type !== 'text') {
    return null;
  }

  const userId = event.source.userId;
  const userMessage = event.message.text.trim();

  if (userMessage === '/start') {
    try {
      const profile = await client.getProfile(userId);
      const name = profile.displayName;

      db.run(
        `INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)`,
        [userId, name],
        function (err) {
          if (err) {
            console.error('❌ 寫入錯誤：', err.message);
          } else {
            console.log(`✅ 使用者資料寫入成功，影響列數：${this.changes}`);
          }
        }
      );

      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: `歡迎你，${name}！你已成功註冊。`
      });
    } catch (error) {
      console.error('❌ 取得使用者資料錯誤：', error);
      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: '抱歉，無法取得您的資料，請稍後再試。'
      });
    }
  }

  return client.replyMessage(event.replyToken, {
    type: 'text',
    text: '請輸入 /start 註冊成為會員'
  });
}

// 新增這個 API，方便查 users 表內容
app.get('/check-users', (req, res) => {
  db.all('SELECT * FROM users', [], (err, rows) => {
    if (err) {
      console.error('查詢 users 錯誤:', err.message);
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});
