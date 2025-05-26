require('dotenv').config();
const express = require('express');
const line = require('@line/bot-sdk');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// LINE Bot 憑證設定
const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.CHANNEL_SECRET
};

const client = new line.Client(config);
const app = express();
app.use(bodyParser.json());

// 📁 SQLite 主資料庫路徑（含 users / vocabulary / learning_status）
const dbPath = path.join(__dirname, 'vocabulary.db');

// 建立 users 資料表（含 user_id, display_name, join_date）
const initUserTable = () => {
  const db = new sqlite3.Database(dbPath);
  db.run(`CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    join_date TEXT
  )`);
  db.close();
};

// Webhook 處理
app.post('/webhook', line.middleware(config), async (req, res) => {
  const events = req.body.events;

  for (const event of events) {
    if (event.type === 'message' && event.message.type === 'text') {
      const userId = event.source.userId;
      const text = event.message.text.toLowerCase();

      if (text === '/start') {
        // 取得使用者資料
        try {
          const profile = await client.getProfile(userId);
          const displayName = profile.displayName;

          const db = new sqlite3.Database(dbPath);
          db.run(
            `INSERT OR IGNORE INTO users (user_id, display_name, join_date) VALUES (?, ?, datetime('now'))`,
            [userId, displayName],
            (err) => {
              if (err) console.error('🚫 儲存使用者失敗:', err.message);
              else console.log(`✅ 使用者儲存成功：${displayName}`);
            }
          );
          db.close();

          // 回覆歡迎訊息
          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: `📘 歡迎使用英文單字推播機器人，${displayName}！我們會每天幫你複習單字。請持續關注～`
          });

        } catch (err) {
          console.error('🚫 無法取得使用者資訊：', err);
        }
      }

      // 你可以在這裡繼續擴充其他指令
    }
  }

  res.status(200).end();
});

// 初始化 & 啟動伺服器
initUserTable();
const PORT = 8000;
app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動中：http://localhost:${PORT}`);
});
