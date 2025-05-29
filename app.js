HEAD
const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
require('dotenv').config(); // 載入環境變數

console.log('🔍 LINE_CHANNEL_SECRET:', process.env.LINE_CHANNEL_SECRET);
console.log('🔍 LINE_CHANNEL_ACCESS_TOKEN:', process.env.LINE_CHANNEL_ACCESS_TOKEN);

const app = express();
const PORT = process.env.PORT || 10000;

// LINE Bot 設定
const config = {
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.LINE_CHANNEL_SECRET,
};

const client = new line.Client(config);

// 初始化資料庫
// 將相對路徑改成絕對路徑（你給的路徑）
const dbPath = 'C:/Users/etien/OneDrive/桌面/linebot-group1-main/vocabulary.db';

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
    db.run(`CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      display_name TEXT,
      join_date TEXT DEFAULT (datetime('now'))
    )`);
  }
});

// webhook 接收
app.post('/webhook', line.middleware(config), (req, res) => {
  console.log('📥 收到 webhook');
  Promise.all(req.body.events.map(handleEvent))
    .then(result => res.json(result))
    .catch(err => {
      console.error('❌ webhook 處理錯誤：', err);
      res.status(500).end();
    });
});

// 處理事件
async function handleEvent(event) {
  console.log('👉 收到事件：', JSON.stringify(event, null, 2));

  if (event.type !== 'message' || event.message.type !== 'text') {
    return null;
  }

  const userId = event.source.userId;
  const userMessage = event.message.text.trim();
  console.log(`📨 來自 ${userId} 的訊息：${userMessage}`);

  if (userMessage === '/start') {
    try {
      const profile = await client.getProfile(userId);
      const name = profile.displayName;

      console.log('✅ 觸發 /start 指令');
      console.log('👤 使用者名稱：', name);
      console.log('📌 嘗試寫入資料：', userId, name);

      db.run(
        `INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)`,
        [userId, name],
        function (err) {
          if (err) {
            console.error('❌ 寫入錯誤：', err.message);
          } else {
            console.log(`✅ 使用者儲存成功（影響列數：${this.changes}）`);

            // 印出 users 表目前所有資料
            db.all(`SELECT * FROM users`, [], (err, rows) => {
              if (err) {
                console.error('❌ 查詢 users 錯誤：', err.message);
              } else {
                console.log('📄 目前使用者資料表內容：');
                rows.forEach(row => {
                  console.log(`👤 ${row.user_id} | ${row.display_name} | ${row.join_date}`);
                });
              }
            });
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

// 定時 log 檢查 server 是否活著
setInterval(() => {
  console.log('🟢 Bot still running at', new Date().toLocaleString());
}, 60000);

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});

const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
require('dotenv').config(); // 載入環境變數

console.log('🔍 LINE_CHANNEL_SECRET:', process.env.LINE_CHANNEL_SECRET);
console.log('🔍 LINE_CHANNEL_ACCESS_TOKEN:', process.env.LINE_CHANNEL_ACCESS_TOKEN);

const app = express();
const PORT = process.env.PORT || 10000;

// LINE Bot 設定
const config = {
  channelAccessToken: process.env.LINE_CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.LINE_CHANNEL_SECRET,
};

const client = new line.Client(config);

// 初始化資料庫
// 將相對路徑改成絕對路徑（你給的路徑）
const dbPath = 'C:/Users/etien/OneDrive/桌面/linebot-group1-main/vocabulary.db';

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
    db.run(`CREATE TABLE IF NOT EXISTS users (
      user_id TEXT PRIMARY KEY,
      display_name TEXT,
      join_date TEXT DEFAULT (datetime('now'))
    )`);
  }
});

// webhook 接收
app.post('/webhook', line.middleware(config), (req, res) => {
  console.log('📥 收到 webhook');
  Promise.all(req.body.events.map(handleEvent))
    .then(result => res.json(result))
    .catch(err => {
      console.error('❌ webhook 處理錯誤：', err);
      res.status(500).end();
    });
});

// 處理事件
async function handleEvent(event) {
  console.log('👉 收到事件：', JSON.stringify(event, null, 2));

  if (event.type !== 'message' || event.message.type !== 'text') {
    return null;
  }

  const userId = event.source.userId;
  const userMessage = event.message.text.trim();
  console.log(`📨 來自 ${userId} 的訊息：${userMessage}`);

  if (userMessage === '/start') {
    try {
      const profile = await client.getProfile(userId);
      const name = profile.displayName;

      console.log('✅ 觸發 /start 指令');
      console.log('👤 使用者名稱：', name);
      console.log('📌 嘗試寫入資料：', userId, name);

      db.run(
        `INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)`,
        [userId, name],
        function (err) {
          if (err) {
            console.error('❌ 寫入錯誤：', err.message);
          } else {
            console.log(`✅ 使用者儲存成功（影響列數：${this.changes}）`);

            // 印出 users 表目前所有資料
            db.all(`SELECT * FROM users`, [], (err, rows) => {
              if (err) {
                console.error('❌ 查詢 users 錯誤：', err.message);
              } else {
                console.log('📄 目前使用者資料表內容：');
                rows.forEach(row => {
                  console.log(`👤 ${row.user_id} | ${row.display_name} | ${row.join_date}`);
                });
              }
            });
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

// 定時 log 檢查 server 是否活著
setInterval(() => {
  console.log('🟢 Bot still running at', new Date().toLocaleString());
}, 60000);

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});
7fe0426 (更新專案程式碼與設定檔)
