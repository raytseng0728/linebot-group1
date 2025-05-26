require('dotenv').config();
const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.CHANNEL_SECRET
};

const client = new line.Client(config);
const app = express();

// 不要用 app.use(bodyParser.json());

const dbPath = path.join(__dirname, 'vocabulary.db');

const initUserTable = () => {
  const db = new sqlite3.Database(dbPath);
  db.run(`CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    join_date TEXT
  )`);
  db.close();
};

app.post('/webhook', line.middleware(config), async (req, res) => {
  const events = req.body.events;

  for (const event of events) {
    if (event.type === 'message' && event.message.type === 'text') {
      const userId = event.source.userId;
      const text = event.message.text.toLowerCase();

      if (text === '/start') {
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

          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: `📘 歡迎使用英文單字推播機器人，${displayName}！我們會每天幫你複習單字。請持續關注～`
          });
        } catch (err) {
          console.error('🚫 無法取得使用者資訊：', err);
        }
      }
    }
  }

  res.status(200).end();
});

initUserTable();

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動中：http://localhost:${PORT}`);
});
