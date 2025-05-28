require('dotenv').config();
const express = require('express');
const line = require('@line/bot-sdk');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const baseDir = __dirname;
const dbPath = path.join(baseDir, 'vocabulary.db');

// 印出目前使用中的資料庫路徑
console.log('🔍 使用中的資料庫路徑：', dbPath);

// 列出目前資料夾中所有 .db 檔案
console.log('📁 專案中發現的 .db 檔案：');
fs.readdirSync(baseDir)
  .filter(file => file.endsWith('.db'))
  .forEach(file => {
    const fullPath = path.join(baseDir, file);
    console.log(`- ${file} ➜ 絕對路徑：${fullPath}`);
  });

const config = {
  channelAccessToken: process.env.CHANNEL_ACCESS_TOKEN,
  channelSecret: process.env.CHANNEL_SECRET
};

const client = new line.Client(config);
const app = express();

// 封裝 sqlite3 的 run 為 Promise
function runAsync(db, sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve(this);
    });
  });
}

// 封裝 sqlite3 的 all 為 Promise
function allAsync(db, sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

// 初始化 users 資料表
function initUserTable() {
  const db = new sqlite3.Database(dbPath);
  db.run(`CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT,
    join_date TEXT DEFAULT (datetime('now'))
  )`, (err) => {
    if (err) {
      console.error('❌ 建立 users 資料表失敗:', err.message);
    } else {
      console.log('✅ users 資料表確認完成');
    }
  });
  db.close();
}

// Webhook 處理邏輯
app.post('/webhook', line.middleware(config), async (req, res) => {
  console.log('📥 收到 webhook');
  const events = req.body.events;

  for (const event of events) {
    console.log('👉 收到事件：', JSON.stringify(event, null, 2));

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

          try {
            // 確認資料表是否存在
            const tables = await allAsync(db, `SELECT name FROM sqlite_master WHERE type='table'`);
            console.log('📋 資料庫內的資料表：', tables.map(t => t.name).join(', '));

            await runAsync(db,
              `INSERT OR IGNORE INTO users (user_id, display_name) VALUES (?, ?)`,
              [userId, displayName]);

            console.log(`✅ 使用者儲存成功：${displayName}`);

            await client.replyMessage(event.replyToken, {
              type: 'text',
              text: `📘 歡迎使用英文單字推播機器人，${displayName}！我們會每天幫你複習單字。請持續關注～`
            });
            console.log('✅ 已送出歡迎訊息');

          } catch (dbErr) {
            console.error('🚫 儲存使用者失敗:', dbErr.message);
            await client.replyMessage(event.replyToken, {
              type: 'text',
              text: `❌ 儲存使用者時發生錯誤，請稍後再試。`
            });
          } finally {
            db.close();
          }

        } catch (err) {
          console.error('🚫 發生錯誤：', err);
          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: `❌ 無法取得使用者資訊，請稍後再試。`
          });
        }
      }

      else if (text === '/showusers') {
        console.log('✅ 觸發 /showusers 指令');
        const db = new sqlite3.Database(dbPath);
        try {
          const rows = await allAsync(db, `SELECT display_name, join_date FROM users ORDER BY join_date ASC`);
          if (rows.length === 0) {
            await client.replyMessage(event.replyToken, {
              type: 'text',
              text: '目前資料庫沒有使用者資料。'
            });
          } else {
            const userList = rows
              .map((row, i) => `${i + 1}. ${row.display_name} (加入於 ${row.join_date})`)
              .join('\n');
            await client.replyMessage(event.replyToken, {
              type: 'text',
              text: `📋 使用者列表：\n${userList}`
            });
          }
        } catch (err) {
          console.error('🚫 查詢使用者失敗:', err.message);
          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: '❌ 查詢使用者失敗'
          });
        } finally {
          db.close();
        }
      }
    }
  }

  res.status(200).end();
});

// 建立 users 表
initUserTable();

// 啟動伺服器
const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`🚀 LINE Bot 伺服器啟動：http://localhost:${PORT}`);
});
