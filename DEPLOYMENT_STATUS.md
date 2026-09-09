# 正式部署交接（2026-09-07）

**網站已發布並完成線上驗證。**

最新公開攻略為293組、734個畫面引用。下文294組／740引用與學生同文對照是歷史來源查證紀錄；使用者已要求攻略移除不存在的學生版流程。

- 攻略：https://wackyjazz.github.io/softlipa_canal/
- 歌詞閱讀：https://wackyjazz.github.io/softlipa_canal/lyrics/index.html
- 素材圖庫：https://wackyjazz.github.io/softlipa_canal/collection/index.html
- GitHub：https://github.com/wackyjazz/softlipa_canal
- 本次 Pages 成功流程：https://github.com/wackyjazz/softlipa_canal/actions/runs/34101037780
- 圖片 Worker：https://canal-guide-images.wackyjazz1.workers.dev（僅允許合法 Referer 及 /images/清單內檔名；缺少 Referer 回403，合法來源的不存在路徑回404）
- Worker Version：94774cc6-d437-4f7e-8a4f-5da5c4e085a5
- 部署頁面 commit：82588f26340bf79a025feef171177ecf2bd5f986；之後的文件與驗證報告 commit 不改動網站內容。

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

最後驗證時間：2026-09-07T08:35:51.914746+00:00

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

## GorDoN 夜店實測說明

新增 https://wackyjazz.github.io/softlipa_canal/verification/gordon-nightclub/index.html 。原始碼及10組隔離原版引擎狀態確認：未完成「嘶」變身，夜店不生成GorDoN；學生版僅在原文資料中，正常流程不可達。附未變身空位／已變身楊教授的兩張無損WebP對照，No274/275新增查證入口，No275明確標記原檔保留、不會正常出現。

本次Pages run 34097704590，內容commit f425379。734張原事件截圖及740個引用皆未變；新增2張查證圖由Pages提供，不修改R2/Worker設定。

線上390/1440px的No275標示、查證入口、兩張1200px圖片與六句原文均驗收通過，報告verification/gordon-audit-web-live-checks.json。

## 原遊戲 favicon

全站5頁使用原始canal-legend.ico作為favicon，原樣保留104,744bytes。線上檔案SHA256與原檔相同，Content-Type為image/vnd.microsoft.icon，各頁相對連結均正確。報告verification/favicon-live-checks.json。內容commit47f9582，Pages run34098025647。後續重新生成頁面可執行guide_tools/site_icons.py；部署包生成時亦會自動同步。

## 攻略內容整理與支線排序

公開攻略排除No275，搜尋/支線/相關事件/進度/統計同步為293組，734張圖與R2設定不變。楊教授只說明輸入「嘶」完成變身與第10章夜店相遇條件。移除程式查證入口及學生版對照說明；舊No275與查證頁連結導向No274。內部原始資料維持294組，避免破壞來源與原始編號。

時空旅人一平移至支線手帖最後SIDE NOTE / 04，前面依序是GorDoN、三種籤、夜店。內容commit a37841b，Pages run34100142025。

線上390/1920px驗收通過：一平為最後SIDE NOTE / 04、公開293組、Gina只命中楊教授、舊連結導向正確、無學生版與查證入口。verification/player-guide-live-checks.json。

## 對話查圖快捷詞

一平快捷按鈕改成MJ與媽媽；目前順序Gina、MJ、媽媽、非工作人員，輸入框範例同步。僅改推薦查詢，不刪除一平事件或搜尋能力。內容commit82588f2，Pages run34101037780。

線上已驗證4個快捷按鈕順序與MJ/媽媽皆有搜尋結果：verification/dialogue-shortcuts-live-checks.json。

## Worker Referer 防盜連（已上線）

Worker先解析Referer，僅接受origin=https://wackyjazz.github.io；缺少、無效、非HTTPS、其他網域/子域/非標準port都先回403，Cache-Control:no-store，不查快取、不讀R2。URL精確比對避免wackyjazz.github.io.evil.example等相似前綴。正常GET/HEAD/304及既有canonical快取規則不變。

Worker版本94774cc6-d437-4f7e-8a4f-5da5c4e085a5；8個單元測試通過，線上允許origin-only及完整站內Referer，無Referer/外站/相似網域回403。正式站首頁、對話、原圖、手機與圖庫瀏覽器驗證通過，報告verification/referer-live-checks.json與verification/referer-site-live-checks.json。

減少的是非授權來源的R2讀取；被拒請求仍計入Workers每日請求額度，Referer亦可被非瀏覽器工具偽造，不能當成認證。直接貼圖片網址、移除Referer的工具、file://或其他host使用線上R2圖將被拒。維護驗證HTTP請求需加Referer（guide_tools/verify_live_images.py已調整）。未啟用付費服務、沒有新增R2物件；這次無需重新部署Pages。

官方額度依據：https://developers.cloudflare.com/workers/platform/pricing/ （Inbound requests to your Worker）。


## 2026-09-08 每日訪客計數

新增首頁今日訪客，三頁共用每日匿名去重計數。D1 canal-guide-visitors；Worker 版本 f871a034-1eae-4374-b1ec-a74b4e047a18。維持 Workers Free，未升級付費。Web Analytics 尚未啟用（RUM API 403）。設定、額度、停用及後續維護見 cloudflare/VISITORS.md（部署資料夾內）。

已正式上線：Pages commit `6b98325a88d5b6f2cda42b3bb67771ee63bec555`；成功部署 https://github.com/wackyjazz/softlipa_canal/actions/runs/34175692834。手機 390px／桌面 1920px、跨頁共用與 API 去重驗證通過。計數從 2026-09-08 開始，無歷史回填。


## 2026-09-08 Cloudflare Web Analytics

使用者提供公開 beacon 後，已加入首頁、圖庫、歌詞三頁，來源 guide/ 與部署 web/ 同步。內容 commit `caae324`；Pages 成功部署 https://github.com/wackyjazz/softlipa_canal/actions/runs/34197835854 。

三頁正式瀏覽器驗證各自只載入一次 beacon（HTTP 200），Cloudflare RUM 收集端均回傳成功（HTTP 204；OPTIONS 200）。報告：部署 repo `verification/beacon-live-checks.json`。後台報表尚未登入查驗；Web Analytics 與 D1 今日訪客為獨立統計。本次只部署 Pages，Worker／D1／R2 設定未變。


## 2026-09-09 石牌文字典藏（已上線）

原始設計典藏新增署名佚名的〈談選擇〉四篇：東區之一、安平之二、北區之三、南區之四，目錄共542項。首頁新增石牌入口，圖庫支援分類、全文搜尋、橫排原文閱讀、下載、收藏與深連結。來源原文及分行保留，縮圖沿用原始石牌底圖。

內容commit `78ac50d`，Pages成功流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34299913319 。線上390px／1440px四篇全文、捲到底、收藏重整、深連結、照片回歸與首頁入口驗證通過，四個正式原文下載逐位元核對一致。報告 `verification/stele-live-checks.json`。原始擷取與維護見HANDOFF_ASSETS_AND_WEB.md最後一節。本次未變更Worker／R2／D1；visitors.js及beacon保留。


## 2026-09-09 石牌翻頁（已上線）

石牌預設為原底圖／像素字型的金色直排翻頁模式，保留橫排原文、下載及收藏。分頁與原始遊戲程式比對一致（2／2／5／5頁）。左鍵下一頁、右鍵上一頁，可放大，模式切換保留頁次，網址支援直接開啟指定頁及原文模式。

內容commit `bf46be9`，Pages成功流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34300469720 。正式站390/1440px每篇每頁、鍵盤及按鈕邊界、原文切換、放大、深連結重整與照片回歸通過，報告verification/stele-pages-live-checks.json。維護方式见HANDOFF_ASSETS_AND_WEB.md最後一節。僅部署Pages，沒有Worker／R2／D1變更。


## 2026-09-09 完整主線攻略與流程圖（已上線）

正式入口：https://wackyjazz.github.io/softlipa_canal/walkthrough/index.html#ch01 。涵蓋10章主線、歸還錦囊與通關後兩節，共58個連續步驟與152個對話截圖連結。每章流程圖可點到對應文字步驟，明示前置条件、交談對象、解鎖結果、分支與卡關檢查；另有瀏覽器進度勾選與夜店交談清單。首頁主按鈕、主要導覽、章節概覽已連接新頁。

內容commit `8822f6f`，Pages成功流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34306324277 。正式站390/1440px全12節、58節點、精確步驟重整、勾選持久化、分支文字、首頁入口與實際1200px對話截圖連結驗證通過。報告verification/walkthrough-live-checks.json。原始場景條件隔離執行報告verification/walkthrough-gate-checks.json；已核對原始規則，但尚未從新遊戲全程實玩，頁面整理依據亦明確標示。

重建及來源維護見HANDOFF_ASSETS_AND_WEB.md最後一節。原圖鑑293事件、734截圖及石牌雙模式保留；沒有Worker／R2／D1變更。新頁沿用visitors.js與beacon。
