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

// 使用 line.middleware 會自動解析 JSON，所以不用 body-parser
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
          db.run(
            `INSERT OR IGNORE INTO users (user_id, display_name, join_date) VALUES (?, ?, datetime('now'))`,
            [userId, displayName],
            async (err) => {
              if (err) {
                console.error('🚫 儲存使用者失敗:', err.message);
                // 回覆錯誤訊息
                await client.replyMessage(event.replyToken, {
                  type: 'text',
                  text: `❌ 儲存使用者時發生錯誤，請稍後再試。`
                });
              } else {
                console.log(`✅ 使用者儲存成功：${displayName}`);
                await client.replyMessage(event.replyToken, {
                  type: 'text',
                  text: `📘 歡迎使用英文單字推播機器人，${displayName}！我們會每天幫你複習單字。請持續關注～`
                });
                console.log('✅ 已送出歡迎訊息');
              }
              db.close();
            }
          );
        } catch (err) {
          console.error('🚫 發生錯誤：', err);
          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: `❌ 無法取得使用者資訊，請稍後再試。`
          });
        }
      }
      else if (text === '/showusers') {
        // 新增 /showusers 指令，查詢所有使用者並回覆清單
        try {
          const db = new sqlite3.Database(dbPath);
          db.all(`SELECT display_name, join_date FROM users`, [], async (err, rows) => {
            if (err) {
              console.error('🚫 查詢使用者錯誤:', err.message);
              await client.replyMessage(event.replyToken, {
                type: 'text',
                text: '❌ 查詢使用者資料失敗'
              });
            } else {
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
                  text: `📋 目前資料庫使用者列表：\n${userList}`
                });
              }
            }
            db.close();
          });
        } catch (err) {
          console.error('🚫 /showusers 發生錯誤：', err);
          await client.replyMessage(event.replyToken, {
            type: 'text',
            text: `❌ 查詢使用者時發生錯誤，請稍後再試。`
          });
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
