require('dotenv').config();
const express = require('express');
const line = require('@line/bot-sdk');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// 設定 LINE Bot 憑證
const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.CHANNEL_SECRET
};

const client = new line.Client(config);
const app = express();
app.use(bodyParser.json());

// SQLite 使用者資料庫路徑
const usersDbPath = path.join(__dirname, 'db/users.db');

// 建立使用者資料表（第一次啟動會建立）
const initUserTable = () => {
  const db = new sqlite3.Database(usersDbPath);
  db.run(`CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    join_date TEXT
  )`);
  db.close();
};

// Webhook 路由
app.post('/webhook', line.middleware(config), async (req, res) => {
  const events = req.body.events;
  for (const event of events) {
    if (event.type === 'message' && event.message.type === 'text') {
      const userId = event.source.userId;
      const text = event.message.text.toLowerCase();

      // 回應 /start 指令
      if (text === '/start') {
        await client.replyMessage(event.replyToken, {
          type: 'text',
          text: '📘 歡迎使用英文單字推播機器人！我們會每天幫你複習單字。請持續關注～'
        });

        // 儲存用戶資訊
        const db = new sqlite3.Database(usersDbPath);
        db.run(`INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, datetime('now'))`, [userId], (err) => {
          if (err) console.error('儲存使用者失敗:', err);
        });
        db.close();
      }

      // 你可以在這裡擴充其他指令，例如 /review, /progress 等
    }
  }
  res.status(200).end();
});

// 初始化並啟動伺服器
initUserTable();
const PORT = 8000;
app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動中：http://localhost:${PORT}`);
});
