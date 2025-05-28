const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

const app = express();
const port = 10000;

// LINE Bot 設定
const config = {
  channelAccessToken: '你的 Channel Access Token',
  channelSecret: '你的 Channel Secret'
};
const client = new line.Client(config);

// 連接資料庫
const dbPath = path.resolve(__dirname, 'vocabulary.db');
console.log('🔍 使用中的資料庫路徑：', dbPath);
console.log('📁 專案中發現的 .db 檔案：');
fs.readdirSync(__dirname).forEach(file => {
  if (file.endsWith('.db')) {
    console.log(`- ${file} ➜ 絕對路徑：${path.resolve(__dirname, file)}`);
  }
});
const db = new sqlite3.Database(dbPath);

// 建立 users 資料表（若尚未存在）
db.run(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT
  )
`, () => {
  console.log('✅ users 資料表確認完成');
});

// Webhook 接收處理
app.post('/webhook', line.middleware(config), (req, res) => {
  Promise.all(req.body.events.map(handleEvent))
    .then(result => res.json(result))
    .catch(err => {
      console.error('❌ 處理事件時出錯：', err);
      res.status(500).end();
    });
});

// 處理事件主體
async function handleEvent(event) {
  if (event.type !== 'message' || event.message.type !== 'text') {
    return null;
  }

  const userId = event.source.userId;
  const userMessage = event.message.text;

  if (userMessage === '/start') {
    const profile = await client.getProfile(userId);
    const name = profile.displayName;

    console.log(`👤 使用者名稱：${name}`);

    db.run(`
      INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)
    `, [userId, name], (err) => {
      if (err) {
        console.error('❌ 寫入使用者資料時出錯：', err.message);
      } else {
        console.log(`✅ 使用者儲存成功：${name}`);
      }
    });

    return client.replyMessage(event.replyToken, {
      type: 'text',
      text: `歡迎你，${name}！你已成功註冊。`
    });

  } else if (userMessage === '/showusers') {
    console.log('✅ 觸發 /showusers 指令');

    return new Promise((resolve, reject) => {
      db.all(`SELECT name FROM users`, [], (err, rows) => {
        if (err) {
          console.error('❌ 查詢使用者時出錯：', err.message);
          return reject(err);
        }

        const userList = rows.map(row => `- ${row.name}`).join('\n') || '（目前沒有使用者）';

        client.replyMessage(event.replyToken, {
          type: 'text',
          text: `👥 所有註冊使用者：\n${userList}`
        }).then(resolve).catch(reject);
      });
    });

  } else {
    return client.replyMessage(event.replyToken, {
      type: 'text',
      text: '請輸入 /start 開始 或 /showusers 查看使用者列表。'
    });
  }
}

// 啟動伺服器
app.listen(port, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${port}`);
});
