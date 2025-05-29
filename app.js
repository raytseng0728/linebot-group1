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

// **務必確認路徑是否存在且可寫**
const dbPath = path.resolve(__dirname, 'vocabulary.db');

console.log('🔍 資料庫路徑:', dbPath);

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('❌ 無法連線到資料庫:', err.message);
    process.exit(1);  // 資料庫開啟失敗就結束程式，避免後面錯誤
  } else {
    console.log('✅ 已連線到資料庫');
    db.run(`CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      display_name TEXT,
      join_date TEXT DEFAULT (datetime('now'))
    )`);
  }
});

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
  console.log('👉 event.source:', event.source);
  if (event.type !== 'message' || event.message.type !== 'text') {
    return null;
  }

  const userId = event.source.userId;
  if (!userId) {
    console.log('⚠️ 無法取得 userId，可能是群組或聊天室事件');
    return null;
  }

  const userMessage = event.message.text.trim();
  console.log(`📨 來自 ${userId} 的訊息：${userMessage}`);

  if (userMessage === '/start') {
    try {
      const profile = await client.getProfile(userId);
      const name = profile.displayName;
      console.log('👤 使用者名稱：', name);

      // 寫入資料庫，Promise 包裝
      await new Promise((resolve, reject) => {
        db.run(
          `INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)`,
          [userId, name],
          function (err) {
            if (err) {
              console.error('❌ 資料庫寫入錯誤:', err.message);
              reject(err);
            } else {
              console.log(`✅ 使用者資料寫入成功，影響列數：${this.changes}`);
              resolve();
            }
          }
        );
      });

      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: `歡迎你，${name}！你已成功註冊。`
      });

    } catch (error) {
      console.error('❌ 取得使用者資料或寫入錯誤：', error);
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

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動，監聽端口: ${PORT}`);
});
