# 正式部署交接（2026-09-07）

**網站已發布並完成線上驗證。**

- 攻略：https://wackyjazz.github.io/softlipa_canal/
- 歌詞閱讀：https://wackyjazz.github.io/softlipa_canal/lyrics/index.html
- 素材圖庫：https://wackyjazz.github.io/softlipa_canal/collection/index.html
- GitHub：https://github.com/wackyjazz/softlipa_canal
- 本次 Pages 成功流程：https://github.com/wackyjazz/softlipa_canal/actions/runs/34096161132
- 圖片 Worker：https://canal-guide-images.wackyjazz1.workers.dev（只接受 /images/清單內檔名；根路徑 404 是預期行為）
- Worker Version：49d977af-71a0-48ce-9668-4ff0540502f5
- 部署頁面 commit：eab586e2d9ae9331e5abdc72d51ed986f7570122；之後的文件與驗證報告 commit 不改動網站內容。

## 已驗證

294 組事件、740 個 frame references、734 張截圖檔名；R2 去重為 733 個物件，共 117,912,963 bytes。每個遠端物件已核對大小、單次 PUT MD5 ETag、Content-Type，本機來源以 SHA-256 驗證。開場、GorDoN、083 截圖從實際 Worker GET 後又比對 SHA-256。

線上瀏覽器已驗證 Gina → No274 第5張、重整維持深連結、No275 教授同文對照、083 關鍵字、538 項素材圖庫的11張照片／放大／深連結、390px手機版與返回攻略；無 JS 錯誤。

## 免費條件與設定

使用者明確確認 Workers Free。帳單 API 無讀取權限，方案狀態依使用者確認，並未自行更改訂閱。R2 使用私人 Standard bucket `canal-guide-images`（APAC），r2.dev disabled、沒有 custom domain。Egress 免費；儲存與讀寫仍按官方免費額度判斷，不能將來無限使用都保證零帳單。

R2 Account ID：10e29bccc61ef294e6cd624a26101d15。Worker 沒有付費圖片轉換、其他資料服務或自動重試。GitHub Secrets 不包含 Cloudflare token；只設公開 repo variable R2_IMAGE_BASE。圖庫約55MiB在Pages，完整素材包的音訊不在網站。

## 後續更新

本機 Git repo 在 `deploy/github-r2`，origin/main 對應上述 repo。GitHub CLI 在 `tmp/deploy-tools/gh`。Wrangler 以 Windows Node 執行，已登入；本機 OAuth 設定不能提交、印出或複製进 repo。

先更新資料並使用原本生成工具刷新 web/ 與 r2-images/，再依序：

1. `tools/upload_r2_oauth.py` 預設只有本機檢查；需要上傳時提供 --apply --free-account-confirmed --account 與 --auth-file（本機 Wrangler OAuth 設定）。733張圖未變更時會校验後跳過，不重傳、不刪舊圖。保留 .upload-ledger.json 的操作預算。
2. 在 cloudflare/ 執行 Wrangler deploy，確認 image manifest 與bucket同步。
3. Git commit / push main；只有手動觸發 pages.yml 才會更新網站，push本身不部署。
4. `gh workflow run pages.yml --repo wackyjazz/softlipa_canal --ref main`，等成功後驗收。圖片服務改網址時須更新 R2_IMAGE_BASE。

線上測試程式在工作區 `guide_tools/test_live.cjs` 與 `guide_tools/verify_live_images.py`。CDP使用獨立Edge 9337，不要操作使用者遊戲；Python HTTP驗證使用明確User-Agent，因Cloudflare曾拒絕urllib的預設UA（1010），一般瀏覽器及Node正常。

驗證紀錄：部署repo的 `verification/live-site-checks.json`、`verification/live-image-checks.json` 和 `verification.json`。現有ZIP是上架前快照；後續以GitHub main與工作區檔案為準。重打部署ZIP時必須排除 .git、node_modules、憑證、母檔、_site、_preview。

最後驗證時間：2026-09-07T07:35:43.978Z

## 038／039 與首頁更新

038、039 原始 hallway 互動資料為 walk_up；原截圖工具錯把視線對準左右教室門，已將 object_targets.py 的 class_b / class_c 改為上方牆壁並限定 walk_up，重新擷取2張、壓縮、核對後上傳。網站仍引用733個R2物件，另保留2個舊版本，不會自動刪除。其他738個frame references的圖片雜湊未變。

首頁標題以 CSS display:block 固定「運河」第一行、「散策」橘色第二行；新增蛋堡杜振熙2026《運河》附贈遊戲介紹、非官方攻略說明及 https://rsdr.online/ 官網支持按鈕。CSS和guide-data.js連結加上版本參數以更新快取。

線上1440/390/320px與038、039修正畫面均驗證通過。報告：verification/hallway-home-live-checks.json、verification/hallway-remote-images.json。工作區 test_hallway_home.cjs 可重新驗證。compress_images.cjs 現在支援指定 038-01 039-01 等圖格，只重壓選定檔案並保留其餘紀錄。

## 歌詞頁與首頁圖片自適應

新增 lyrics/index.html，收錄既有遊戲抽取資料的6首457段歌詞，提供12曲目錄（其餘6曲明確標示沒有內嵌歌詞）、搜尋、字級、時間標記、段落深連結。文字與時間逐段比對原始lyrics/lyrics.json相同，沒有新增音樂檔。

首頁圖片改為等比例img，桌面左右排列、900px以下上下排列；不裁切、不遮住人物或對話框，維持運河／橘色散策兩行。新歌詞頁全部檔案合計50,221 bytes，由Pages提供；圖片沿用原R2物件，Worker與bucket設定未改。

歌詞與按鈕版本Pages成功部署34095691131，內容commitd9fa5e4。完整來源、生成方式與驗收指令見HANDOFF_ASSETS_AND_WEB.md最後一節。

官網支持按鈕依最新要求放在介紹下方置中，改亮橘色#ff963f、桌面最大560px寬、最小68px高，文字18px（手機16px），支援換行。

線上已驗證320/390/768/1024/1440/1920px完整圖片等比例顯示與置中橘色大按鈕；歌詞12曲原文、搜尋及段落重整、字級與時間標記均通過。報告：verification/lyrics-scale-live-checks.json。

## 主線路書字級更新

桌面主線路書內文從13px提升為18–22px，章節選單/事件連結從10px提升為16–18px，說明14–16px。保留原雙欄版型，左欄配合字級加寬，901px以上生效。內容commit eab586e，Pages run 34096161132。本次只更新HTML/CSS，沒有變更R2。

線上390/901/1440/1920/2560/3840px的全部12章切換與無溢出驗收通過：verification/route-type-live-checks.json。
