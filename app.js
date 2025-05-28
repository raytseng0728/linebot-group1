const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
console.log('🔍 LINE_CHANNEL_SECRET:', process.env.LINE_CHANNEL_SECRET);
console.log('🔍 LINE_CHANNEL_ACCESS_TOKEN:', process.env.LINE_CHANNEL_ACCESS_TOKEN);

require('dotenv').config(); // 載入環境變數

const app = express();
const PORT = process.env.PORT || 10000;

// LINE Bot 設定，從環境變數讀取
const config = {
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.LINE_CHANNEL_SECRET,
};

const client = new line.Client(config);

// 初始化資料庫
const dbPath = path.join(__dirname, 'vocabulary.db');
console.log('🔍 使用中的資料庫路徑：', dbPath);

console.log('📁 專案中發現的 .db 檔案：');
fs.readdirSync(__dirname)
  .filter(file => file.endsWith('.db'))
  .forEach(file => {
    console.log(`- ${file} ➜ 絕對路徑：${path.join(__dirname, file)}`);
  });

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('❌ 無法連線到資料庫：', err.message);
  } else {
    console.log('✅ 已連線到資料庫');
    // 確保 users 資料表存在
    db.run(`CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      name TEXT
    )`);
  }
});

// 使用 LINE middleware 驗證簽章，並解析事件
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
  console.log('👉 收到事件：', JSON.stringify(event, null, 2));

  if (event.type !== 'message' || event.message.type !== 'text') {
    // 只處理文字訊息
    return null;
  }

  const userId = event.source.userId;
  const userMessage = event.message.text.trim();

  console.log(`📨 來自 ${userId} 的訊息：${userMessage}`);

  if (userMessage === '/start') {
    try {
      // 取得使用者名稱
      const profile = await client.getProfile(userId);
      const name = profile.displayName;

      console.log('✅ 觸發 /start 指令');
      console.log('👤 使用者名稱：' + name);

      // 寫入資料庫（有就忽略）
      db.run(
        `INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)`,
        [userId, name],
        function (err) {
          if (err) {
            console.error('❌ 寫入錯誤：', err.message);
          } else {
            console.log(`✅ 使用者儲存成功：${name}（影響列數：${this.changes}）`);
          }
        }
      );

      // 回覆使用者
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

  // 其他訊息回覆固定文字
  return client.replyMessage(event.replyToken, {
    type: 'text',
    text: '請輸入 /start 註冊成為會員'
  });
}

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});
