# 免費使用的邊界

核對日期：2026-09-07。不能保證服務商未來不改價，也不能把另一個專案的帳單算成這個專案可以控制的事情。

| 項目 | 本包設定 | 官方免費額度／本包限制 |
| --- | --- | --- |
| 網頁 | GitHub Free、公開 repository、github.io | Pages 網站 1 GB；頻寬軟上限 100 GB／月 |
| 圖片儲存 | R2 Standard；約 0.118 GB | 10 GB-month／月；上傳工具保守限制整個 bucket 1 GB |
| 寫入與列出 | 只由本機管理工具執行 | R2 Class A 100 萬次／月；本機工具預算 1 萬次／UTC 月 |
| 圖片請求 | Workers Free；每次最多一個 R2 GetObject | Workers 每日 10 萬次請求；R2 Class B 每月 1,000 萬次 |
| 網域 | github.io、workers.dev | 不購買自訂網域 |
| 圖片流出 | R2 直接經 Worker 傳送 | R2 流出流量免費 |

資料來源：[R2 定價](https://developers.cloudflare.com/r2/pricing/)、[Workers 免費方案請求上限](https://developers.cloudflare.com/workers/platform/limits/#daily-requests)、[GitHub Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。

## 這個設計如何控制用量

**依官方額度推算**：Workers Free 每天最多 100,000 次請求，31 天最多 3,100,000 次。Worker 只做一次 GetObject、不重試、不列出、不寫入，所以本圖片入口的讀取低於 R2 每月 10,000,000 次免費額度。Worker 的 GET 已加快取；HEAD、相同 ETag、非法路徑及寫入请求不讀 R2。快取不是保證免費的唯一防線，每日請求上限才是主要邊界。

必須保留以下條件：

1. **Workers Free，不升級 Paid。** 免費帳號超過每日請求上限會回傳錯誤；圖片暫時無法讀取，不能自動繞到 R2 公開端點。
2. **R2 bucket 保持私人。** r2.dev 與 Custom Domains 都不啟用。否則有人可繞過 Worker，破壞前述讀取上限推算。
3. **只用 Standard。** Infrequent Access 不適用相同免費額度，亦有資料提取費。
4. **帳號的 R2 額度沒有被其他產品耗用。** 建議使用沒有其他 R2 專案的帳號；免費額度不是每個 bucket 都各送一份。
5. **上傳只用受控工具。** 本機預算不涵蓋其他電腦、Console、S3 客戶端或失竊憑證的操作；也不會替全帳號設定硬性金額封頂。工具停用 SDK 自動重試，以免重試產生難以估計的額外操作。
6. **不加付費服務。** 本包未配置 Workers Paid、付費圖片轉換、KV、D1、Durable Objects、持續記錄 Worker logs 或付費網域。

## 不能承諾的事

R2 超過免費額度會計費，本包沒有 Cloudflare 帳號管理權限，不能核實你既有的方案、當期其他用量、公開端點或付款設定。Cloudflare 用量通知亦不等於金額硬上限。[官方用量計費说明](https://developers.cloudflare.com/billing/understand/usage-based-billing/)

因此，這是「在明確條件下可維持 $0 的 GitHub＋R2 配置」，不是對所有帳號狀況的零帳單保證。若你要求完全排除 R2 的計費風險，使用 README 的 **純 GitHub Pages** 版本；它同樣保留對話查圖、原文與全部圖片，且不需開通 R2。
