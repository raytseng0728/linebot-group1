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
  console.log('📥 收到 webhook'); // 確認有收到 LINE 傳來的請求

  const events = req.body.events;

  for (const event of events) {
    console.log('👉 收到事件：', JSON.stringify(event, null, 2)); // 印出事件詳細資料

    if (event.type === 'message' && event.message.type === 'text') {
      const userId = event.source.userId;
      const text = event.message.text.toLowerCase();
      console.log(`📨 來自 ${userId} 的訊息：${text}`);

      if (text === '/start') {
        console.log('✅ 觸發 /start 指令');

        try {
          const profile = await client.getProfile(userId);
          const displayName = profile.displayName;
          console.log(`👤 使用者名稱：${displayName}`);

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

          console.log('✅ 已送出歡迎訊息');
        } catch (err) {
          console.error('🚫 發生錯誤：', err);
        }
      }
    }
  }

  res.status(200).end(); // 回傳成功給 LINE 平台
});
