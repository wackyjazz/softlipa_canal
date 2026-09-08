# 每日訪客計數交接（2026-09-08）

首頁底部顯示全站「今日訪客」估計值。攻略、圖庫、歌詞頁載入共用 `assets/visitors.js`。

- API：現有圖片 Worker 的 `/api/visitors`；D1 binding `VISITORS`，資料庫 `canal-guide-visitors`。
- 日期由伺服器 UTC+8 決定。POST text/plain UUID v4，GET 只讀今日彙總。
- 每日匿名 UUID 存 localStorage `canal-guide-daily-visitor-v1`；每日更換。資料庫 `(day,visitor)` 唯一鍵與 INSERT trigger 保證重試不重複計數。不同裝置／無痕／清除儲存會重算，機器人可偽造識別碼，不能視為精確真人數或帳務依據。
- 本機檔案與其他網域不連正式 API。儲存不可用時僅 GET，不記數。成功回應快取於瀏覽器 5 分鐘，無持續輪詢；切換分頁跨日會更新。失敗顯示暫時無法取得，不影響攻略。
- API 同時限制 Referer 與 Origin 為 https://wackyjazz.github.io，不開放任意來源寫入；此檢查非身分驗證。POST body 最多 128 bytes，無自動重試。
- 每日台灣 00:15 Cron 刪除早於兩日前的匿名識別紀錄，每次上限 5000 列；大量訪客時清理可能落後，日彙總保留供趨勢檢視。不儲存 IP。
- Workers 維持 Free；圖片和計數 API 共用全帳號每日 100,000 請求額度（台灣 08:00 重置）。D1 Free 每日 500 萬列讀／10 萬列寫／總共 5GB；索引、trigger、清理也耗寫入。超額可能暫停功能，沒有升級付費方案。
- R2 計費設定未變。計數不讀寫 R2。Worker 的 R2 圖片保護測試保留。
- Web Analytics：2026-09-08 使用者提供 Cloudflare 後台公開 beacon，已加入攻略、圖庫、歌詞三頁。後台分析與首頁 D1 今日訪客是獨立統計，數字可能不同。

## 驗證與部署

Node 25+ `npm test`：8 項既有圖片測試 + 5 項使用真實 SQLite 的統計測試。
初次部署先 `wrangler d1 execute canal-guide-visitors --remote --file visitors.sql`，再 `wrangler deploy`。Schema 冪等；勿清空正式資料。
網站來源在根目錄 guide/，需同步 deploy/github-r2/web/ 後推送並手動執行 pages.yml。重建圖庫／歌詞 HTML 時保留 visitors.js 與 Cloudflare beacon script。

查看歷日：Cloudflare D1 Console 執行 `SELECT day, visitors FROM daily_totals ORDER BY day DESC LIMIT 30;`。
實際額度使用看 Workers Metrics、R2 Metrics 和 D1 Metrics，訪客不能換算成固定請求數。
停止統計：移除三頁 visitors.js 標籤並部署 Pages；需要完全停用 API 時移除 Worker 的 /api/visitors 路由與 Cron 再部署，保留圖片路由。不要直接停用整個 Worker，否則圖片會失效。
