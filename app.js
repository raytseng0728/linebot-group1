const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

require('dotenv').config(); // 確保載入 .env（本地用）

const app = express();
const PORT = process.env.PORT || 10000;

// 讀取環境變數，並檢查
const CHANNEL_ACCESS_TOKEN = process.env.LINE_CHANNEL_ACCESS_TOKEN;
const CHANNEL_SECRET = process.env.LINE_CHANNEL_SECRET;

if (!CHANNEL_ACCESS_TOKEN || !CHANNEL_SECRET) {
  console.error('❌ 缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET，請檢查環境變數');
  process.exit(1);
}

console.log('✅ LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 已載入');

const config = {
  channelAccessToken: CHANNEL_ACCESS_TOKEN,
  channelSecret: CHANNEL_SECRET,
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
    console.log('✅ users 資料表確認完成');
    db.get("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'", (err, row) => {
      if (row) {
        console.log('🧱 users 資料表結構：', row.sql);
      } else {
        console.log('⚠️ 尚未建立 users 資料表');
      }
    });
  }
});

// 不要加 express.json()
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
      console.log('👤 使用者名稱：' + name);

      db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, tables) => {
        if (err) {
          console.error('❌ 查詢資料表錯誤：', err.message);
        } else {
          console.log('📋 資料庫內的資料表：', tables.map(t => t.name).join(', '));
        }
      });

      console.log('🟡 嘗試寫入使用者到 DB...');
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

      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: `歡迎你，${name}！你已成功註冊。`
      });

    } catch (error) {
      console.error('❌ 取得使用者資料錯誤：', error);
      return client.replyMessage(event.replyToken, {
        type: 'text',
        text: '取得使用者資料失敗，請稍後再試。'
      });
    }
  }

  if (userMessage === '/showusers') {
    console.log('✅ 觸發 /showusers 指令');
    return new Promise((resolve) => {
      db.all(`SELECT * FROM users`, (err, rows) => {
        if (err) {
          console.error('❌ 查詢錯誤：', err.message);
          resolve(client.replyMessage(event.replyToken, {
            type: 'text',
            text: '查詢使用者時發生錯誤'
          }));
        } else {
          console.log('📋 查詢到的使用者資料：', rows);
          if (rows.length === 0) {
            resolve(client.replyMessage(event.replyToken, {
              type: 'text',
              text: '📭 使用者列表為空'
            }));
          } else {
            const userList = rows.map(u => `• ${u.name} (${u.id})`).join('\n');
            resolve(client.replyMessage(event.replyToken, {
              type: 'text',
              text: `📋 使用者列表：\n${userList}`
            }));
          }
        }
      });
    });
  }

  return client.replyMessage(event.replyToken, {
    type: 'text',
    text: '請輸入 /start 或 /showusers'
  });
}

app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});
