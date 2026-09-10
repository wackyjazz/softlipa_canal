# 交接：完整素材擷取與攻略網頁整合

> 正式網站已上線：https://wackyjazz.github.io/softlipa_canal/ 。部署與更新流程請讀 [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)；下文未發布相關敘述是素材包製作階段的歷史記錄。

> 後續部署授權已更新：使用者已要求發布到 wackyjazz/softlipa_canal 與自己的 R2。請先讀 [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)；下文「未授權／未部署」為上一階段歷史狀態。

## 接手先讀

使用者使用繁體中文。這次要求把原本主要是人物的素材包擴充為所有原始設計，包含照片、彩蛋相關物件、塗鴉與場景；接著要求繼續優化網頁，並留下 agent 交接文件。已採取「完整離線素材包 + 攻略內視覺素材圖庫」兩種交付形式。不要將此工作當成重新擷取劇情對話畫面的要求。

**不要改動或關閉使用者的 `gordon_demo`、`gordon_demo_v2` 或其他遊戲實例。不要啟用付費方案或廣泛 kill 同名遊戲程序。** 使用者後續已授權部署，現已上線；請以 DEPLOYMENT_STATUS.md 為準。

目前沒有使用子 agent。請遵守當前對話的代理與權限規則；不需要為本機可回復工作額外要求確認。

## 成品與來源

| 路徑 | 用途 |
| --- | --- |
| `full_asset_pack/index.html` | 完整素材包離線入口，604 項目錄 |
| `full_asset_pack/manifest.json` | 原始 SHA、來源路徑、atlas 座標、動畫序號與程式引用 |
| `full_asset_pack/verification.json` | 原始檔及拆圖驗證 |
| `full_asset_pack/originals/dist/` | 375 個原始資源，逐位元保留 |
| `full_asset_pack/designs/` | 101 個獨立塗鴉 + 101 個遮罩 |
| `full_asset_pack/frames/` | 88 張動畫圖集的 3,202 個非空白 PNG 圖格 |
| `full_asset_pack/scenes/` | 9 張室內 + 18 張戶外日夜底圖合成 |
| `guide/index.html` | 原攻略，新增「原始設計圖庫」段落與導覽 |
| `guide/collection/index.html` | 攻略內圖庫，538 項視覺素材 + 全部圖格 |
| `運河_完整設計素材包.zip` | 完整素材包，解壓後開 index.html |
| `運河散策_完整圖文攻略.zip` | 含內建圖庫的完整攻略 |
| `運河攻略_GitHub_R2部署包.zip` | 更新後本機部署包，尚未發布 |

權威來源為保留的 `accelerated_portable_v2/resources/app.asar.original`，不是魔改版 ASAR。使用 `build_gordon_demo.read_asar()` 讀取；來源檔 SHA 已記錄於 manifest。沒有使用 AI 重畫素材。

收錄原始圖像共 309 個：255 PNG、21 JPG、32 SVG、1 ICO。照片 11 張（`dist/photo`），結尾圖 20 張（`dist/screenshots`）。原始塗鴉的 `dist/gameData/painting.json` 有 101 個 frames，供 `painting.png` 與 `painting-mask.png` 共用。不要只複製 atlas 大圖而漏掉獨立設計。

完整包另含 42 MP3（約 104 MiB）、3 字型、20 JSON 與 1 shader。網頁圖庫只帶視覺資源，避免把音訊與地圖資料整批加入攻略下載。

## 已完成的網頁功能

- 圖庫支援分類、多個空白分隔關鍵字（AND）、中英文關鍵字對照與快速分類。
- 先載入 60 張卡片，按鈕每次增加 60；縮圖使用小尺寸無損 WebP、lazy loading。
- 點圖後才載入完整原尺寸，保留透明背景，支援原尺寸／適合視窗切換。
- 動畫以 range 逐格選取，120 ms 圖格預覽，左右方向鍵切換。
- 收藏 checkbox 寫入 localStorage；可匯出／匯入 Markdown 清單。
- 分類／搜尋寫入 URL query，素材以 `#asset=<encoded file path>` 深連結；可直接複製瀏覽器網址。
- `/` 聚焦素材搜尋、原生 dialog 支援 Escape，手機雙欄無水平溢出。
- 原攻略新增素材導覽與照片／結尾圖／塗鴉／場景 4 個入口；圖庫能返回攻略。
- 完整素材圖庫可離線開啟，不需要 fetch API 讀取本機 JSON；使用 `catalog-data.js`。

## 重建流程

工作目錄 `/mnt/d/wsl_home/rsdr_game`。Python3 標準庫可用，**不要假設 Pillow 已安裝**。目前可用 Windows Node：

```bash
python3 asset_tools/extract_all.py
'/mnt/c/Program Files/nodejs/node.exe' asset_tools/derive.cjs
python3 asset_tools/publish.py
'/mnt/c/Program Files/nodejs/node.exe' asset_tools/verify_pixels.cjs
python3 asset_tools/integrate_guide.py
python3 guide_tools/build_deploy_package.py
python3 guide_tools/package_guides.py
python3 asset_tools/package.py
```

依賴：`derive.cjs` / `verify_pixels.cjs` 使用 `deploy/github-r2/cloudflare/node_modules/sharp`（目前固定 Wrangler 相依套件中的 Sharp）。不需要額外安裝圖像 AI 工具。若依賴未在另一環境安裝，先依該部署資料夾的 package-lock 執行 npm ci。

`extract_all.py` 會重新產生原始 manifest；`derive.cjs` 會重建所有拆圖與預覽；`publish.py` 會重新產生 catalog-data / README / 基礎 verification。**像素驗證應在 publish 後執行，再 integrate，否則後一次 publish 會覆蓋驗證附加欄位。** `integrate_guide.py` 與攻略 section/CSS 插入具重跑防重複判斷。若修改分類、來源檔案或移除資源，現行 copytree 不會清理舊輸出，應先依舊 manifest 精確清掉生成檔，避免把使用者檔案一起刪除。

模板是 `asset_tools/catalog.html`。不要只改生成的 `full_asset_pack/index.html` 或 `guide/collection/index.html`，否則重建會覆蓋。主攻略 section/CSS 插入模板在 `integrate_guide.py`；已插入後若改設計，需同步改攻略及生成腳本。

## 驗證方式

- `publish.py`：375 原始檔與 ASAR 逐位元相同、309 張原始圖像沒有遺漏、所有圖格與預覽連結存在。
- `verify_pixels.cjs`：202 個 atlas 拆圖與 3,202 個動畫 PNG，解碼像素逐一比對原圖對應矩形。
- `asset_tools/test_catalog.cjs`：Edge CDP 瀏覽器檢查 604 項目錄、照片 11 張、原圖載入、Gordon 3 張圖集及第 2 格、HTML 字串搜尋安全、塗鴉 101 張、390px 手機無溢出。
- `asset_tools/test_integration.cjs`：攻略入口、538 項嵌入圖庫、分類網址、深連結與返回攻略。
- 原攻略回歸：`python3 guide_tools/verify.py`、Windows Node `guide_tools/test_site.cjs`。
- ZIP：`asset_tools/package.py` 及 `guide_tools/package_guides.py` 會做 CRC 與所有檔案 SHA 比對。

測試瀏覽器為獨立 Edge headless，CDP **9337**。`guide_tools/cdp.cjs` 的 `connect(9337)` 能直接使用；Windows Node 不一定繼承 WSL 前綴 env vars，請明確傳 port。**不要平行導航同一個 CDP 頁面**。若瀏覽器已關閉，需要另起自己的隔離測試 profile。遊戲擷取則是不同的 9336，目前沒有需要啟動。

## 真實性與限制（務必保留）

- 圖庫是原始設計擷取，不是新增實玩劇情截圖。
- 「彩蛋」關鍵字包括塗鴉、幽靈船、壁虎、專輯、一平等探索線索。**不表示已證實每張圖都有獨立秘密事件**；程式引用 excerpt 可供後續研究。
- 場景只合成可見美術圖層：室內略過碰撞、觸發區及不可見層；戶外將 under/front 同座標相疊。沒有加執行時 NPC、道具、塗鴉、後處理特效或章節條件。章節變體在 originals 中另存。
- 地圖 renderer 支援當前檔案使用的翻轉；現有室內圖只有奶奶家 15 個水平翻轉。若日後延伸到任意 Tiled 地圖，須再驗證 diagonal + flip 的轉換與圖層透明度／group，不要假設通用。
- 動畫按圖格索引順序，不是遊戲的動作狀態機。空白格留在完整原圖集中，不輸出冗餘 PNG。
- Phaser 引擎有 4 處 inline 圖片引用（預設／debug texture 與動態 SVG 模板），記在 manifest；沒有視為遊戲設計輸出。
- 只涵蓋原 ASAR 內本機可用資源；沒有推測伺服器或外部帳號才提供的未知素材。

## 保護先前攻略工作

原攻略仍為 294 組事件、740 個 frame references、734 個獨立截圖。No.275 學生 GorDoN 的 6 句原始台詞與教授版同文，引用 No.274 的教授畫面並明確標註；**不要偽造可實際觸發的學生版**，也不要改寫原始 speaker。程式在相同 `GorDoN` flag 下生 NPC 且選教授台詞。

全部已發布截圖是 `guide/assets/images/*.avif`，1200×900。JPEG 原始母檔在 `capture_masters/images/`，不得放回部署包，勿當成多餘檔刪除。AVIF 全部 734 張共 112.6 MiB，較 JPEG 減少 41.8%，壓縮紀錄與 before/after 比較在 `guide/verification/`。ZIP 大小不等於網頁圖片下載量；PNG/JPEG 可能在 ZIP 內較容易壓縮。

之前花很多時間修正的 NPC 位置、對齊、櫃檯入口與動畫截圖，這次沒有重新擷取或覆蓋。若修改擷取流程，先讀 `guide/verification` 與 `guide_tools` 內既有說明。

## GitHub Pages + R2 邊界

`guide_tools/build_deploy_package.py` 現在把 `guide/collection` 複製到 `deploy/github-r2/web/collection`。新增圖庫為 **GitHub Pages 靜態檔**；R2 Worker 仍只允許原本 734 張攻略截圖的檔名／SHA，不新增 R2 上傳或存取路由。使用者不必為素材圖庫啟用額外付費服務。

`deploy/github-r2/tools/build_site.py` 有 github-only 與 R2 模式。`_site`、`_preview`、node_modules、母檔與本機憑證不進部署 ZIP。新增圖庫之後請重新量測部署總大小，不要沿用先前約 4 MB 靜態頁面的舊數字。

未取得 GitHub repo / Cloudflare 認證，也未部署。R2 使用量計費，不能保證任意流量或共用帳號都永遠零費用；原先 `FREE-TIER.md` 的條件和 upload guard 不要移除。

## 後續可做的具體工作

1. 若使用者要求「彩蛋出現在哪裡」，依每張圖的 references、地圖物件與原遊戲 create 邏輯建立實際座標／章節關係，再連回攻略事件；不要只按檔名猜位置。
2. 若要精確動畫名稱，分析 Phaser anims 定義，將同一圖集拆成 walk/up/down/idle 等原生播放序列。目前只有忠實逐格瀏覽。
3. 若要完整遊戲外觀的城市拼圖，需加入場景 create 中動態裝飾、塗鴉位置與 chapter/night 分支；現有 scenes 已清楚標「底圖合成」，不能直接宣稱實玩全景。
4. 若網頁要更輕，可將視覺原檔另外做無損 WebP 版本，但完整包中的原檔與來源 SHA 必須保留；再量測首屏與點圖下載，避免壓糊文字或像素邊緣。

## 本輪完成檢查紀錄

原檔位元比對、202 張 atlas 像素比對、3,202 格動畫像素比對、素材圖庫瀏覽器測試、攻略整合與深連結測試，以及原攻略 verify.py / test_site.cjs 回歸皆已通過。原攻略仍有 734 張畫面、733 種 SHA，沒有撤回事件或截圖失敗。verify.py 已改以 URL path 驗證本機連結，正確排除新增分類 query。

## 歌詞閱讀與首頁圖片自適應（2026-09-07）

- 首頁 `#hero-art` 使用真正的 img，width:100%、height:auto、object-fit:contain。桌面雙欄，900px以下上下排列，禁止恢復 background-size:cover，以免裁掉場景。固定「運河」第一行、橘色「散策」第二行。
- 新頁 `guide/lyrics/index.html`（部署對應 `web/lyrics/`）。首頁側欄、歌詞段落與6首捷徑均可進入。
- 唯一文字來源為既存 `lyrics/lyrics.json`；`python3 guide_tools/build_lyrics.py` 生成 lyrics-data.js / source.json，完整保留文字、排序、時間及 duration。共12曲，6曲含歌詞，共457段。沒有內嵌歌詞的曲目顯示未收錄，不推定為純音樂，不補寫或抓取外部歌詞，網站沒有新增音訊。
- 歌詞頁支援曲名/歌詞AND搜尋、命中高亮、`#track-09/line-1`段落深連結、上下曲、18/22/28px字級、時間標記及複製連結。設定保存於 canal-lyrics-* localStorage；讀取失敗不影響閱讀。
- `guide_tools/build_deploy_package.py` 已加入 lyrics 目錄複製。僅更新文字/CSS/JS時只需同步到web、commit/push、手動Pages部署，不需R2上傳或Worker部署。
- 驗收工具：`guide_tools/test_lyrics_scale.cjs [baseURL]`，檢查320/390/768/1024/1440/1920px首頁圖片比例、完整可見、無遮擋、無橫向溢出；12曲原文逐段一致、搜尋深連結、重新整理與閱讀設定。`test_hallway_home.cjs` 保留兩行標題與038/039回歸檢查。

- 最新官網支持CTA：專輯介紹下方置中，亮橘色#ff963f、桌面最大560px、最小高度68px、桌面18px/手機16px字體。保持手機自動換行，不要再縮回小型右側按鈕。

## 主線路書大螢幕字級

依使用者要求保留原本雙欄章節版型，只放大901px以上的主線路書文字。選單與事件連結16–18px、內文18–22px、說明14–16px；clamp隨視窗增加。左欄280–360px以容納加大文字，手機沿用原版型。CSS限定#routes避免影響其他區塊。驗證390/901/1440/1920/2560/3840px全部12章切換、無裁切或橫向溢出，報告在verification/route-type-*-checks.json。

## GorDoN 夜店生成重新查證

2026-09-07 再查原始ASAR（SHA256 44d4d25857a4c5f57643846ea4a81bb0e144ffaa780c7fbf08b5abcecc40f1ef），全bundle只找到4處new oe：結尾、夜店生成、夜店聽歌補齊、戶外。夜店兩處都要求GorDoN旗標；旗標唯一add位於triggerGorDoNHenshin完成後，setFinalAnswer精確比對「嘶」進入此流程。triggerGorDoNTalk無NPC先return，有旗標選教授，故學生代號在此版本正常流程不可達。一般夜店兩種旗標皆不生成他；談話/聽歌只有已變身才生成教授。夜店student_1/2/3是其他NPC。

隔離原版引擎9336驗證10組：第10章normal/talking/listening ×有無旗標；11/12章normal ×有無旗標。聽歌是直接呼叫原始交談函式的診斷，不表示聽歌中可正常按鍵交談。沒有插入NPC。音效與過場等待有停用，非全流程通關。guide_tools/audit_gordon_presence.cjs可重跑（須先啟動隔離capture app）；結果guide/verification/gordon-presence-audit.json。已停止本次啟動的精確tmp/guide_capture執行檔，未操作其他遊戲。

公開查證頁guide/verification/gordon-nightclub/index.html，兩張1200x900無損WebP：未變身空位／變身教授原文第一句。新增543,372bytes證據圖片由Pages提供，不列入734張對話截圖或R2清單。No274/275詳情有查證入口，No275標題及提示改成已查證正常流程不出現；原本六張教授同文對照仍明確標記，未造學生圖。原始碼片段與10組驗證JSON放在查證頁同目錄；build_deploy_package.py已加入其複製。

## 原遊戲 favicon

全站5個HTML入口改用favicon.ico，原檔來自accelerated_portable_v2/resources/icon/canal-legend.ico，SHA256 4c7848a33217a7b75f7bd9869c1b63f4e5a355db05e24ad06564a904abbe4fdb，與素材包ICO一致，未重畫或轉檔。guide_tools/site_icons.py同步原ICO並設定各頁相對路徑及雜湊版號；build_deploy_package.py在複製前自動執行，避免重新生成圖庫或驗證頁時遺漏圖示。由Pages提供，無R2變更。

## 最新編輯方針：攻略只呈現玩家能遇到的內容

使用者明確要求移除「夜店學生GorDoN：原檔保留」等不存在流程與程式解釋。publish.py從public_events排除e275；公開293組、730段對話+4選項回覆=734個frame引用，734張檔案/733個R2物件不變。其餘事件編號不重排。原始294組events.json/dialogues.json/captures.json留作內部來源，不得又拿來源筆數當公開攻略收錄數。public related、支線推薦、搜尋、coverage、進度分母同步293。No274只保留輸入「嘶」完成變身、第10章夜店相遇的玩家條件。

移除No274/275的查證入口、學生版說明、教授同文對照推薦。程式查證材料移到本機research/gordon-nightclub；公開舊查證HTML僅轉到#e274，移除公開audit/source JSON及兩張比較圖。舊#e275[/frame/N]轉到#e274[/frame/N]，既有其他筆記與編號維持。README與首頁關於段落改成玩家用法。

tmp/check_player_guide.cjs驗證293筆、Gina只命中楊教授第5張、手機/桌面、舊網址導回正確攻略。既有test_live.cjs/test_site.cjs的No275斷言已配合更新。未增加不存在的學生服截图。

使用者最新順序：支線手帖為GorDoN、三種籤、夜店、一平；時空旅人一平固定最後SIDE NOTE / 04。publish.py輸出順序已更新，不能只改生成後資料。

## 圖片 Worker Referer 防盜連

使用者授權僅允許wackyjazz.github.io來源以减少盜連讀取。cloudflare/worker.mjs在URL/快取/R2處理前，以URL解析Referer並精確比對origin=https://wackyjazz.github.io。缺少/無效/非HTTPS/其他host或非標準port一律403且Cache-Control:no-store，包括HEAD與If-None-Match。正常請求維持既有canonical快取、HEAD/304零R2讀取、GET最多1次R2讀取。新增測試覆蓋12種拒絕來源×GET/HEAD及允許origin-only/完整路徑，8項測試通過。

這是一般防盜連，不是認證：Referer可偽造，被拒請求仍計入Workers請求額度，但沒有R2讀取。嚴格模式會拒絕直接貼圖片網址、移除Referer的隱私工具、file://或其他host預覽使用線上R2圖；正式Pages網站瀏覽器會提供允許的origin。真正完整離線包自帶本機圖，不受影響。維護HTTP驗證需提供允許的Referer，guide_tools/verify_live_images.py已更新。使用者沒有授權升級付費方案，不需要新增服務。


## 2026-09-08 每日訪客計數

新增首頁今日訪客，三頁共用每日匿名去重計數。D1 canal-guide-visitors；Worker 版本 f871a034-1eae-4374-b1ec-a74b4e047a18。維持 Workers Free，未升級付費。Web Analytics 尚未啟用（RUM API 403）。設定、額度、停用及後續維護見 cloudflare/VISITORS.md（部署資料夾內）。

已正式上線：Pages commit `6b98325a88d5b6f2cda42b3bb67771ee63bec555`；成功部署 https://github.com/wackyjazz/softlipa_canal/actions/runs/34175692834。手機 390px／桌面 1920px、跨頁共用與 API 去重驗證通過。計數從 2026-09-08 開始，無歷史回填。


## 2026-09-09 石牌〈談選擇〉典藏

從保留的原始 ASAR `dist/assets/index-BbZAngKC.js` 擷取四個石牌文字陣列，並以原始地圖互動物件確認位置：東區之一（原題「之ㄧ」）、安平之二、北區之三、南區之四，署名均為佚名。舊圖庫只有 stele.png 底圖，現補原文閱讀與四筆典藏，網頁從538項增加至542項，完整素材包从604項增加至608項。

首頁新增四篇石牌專用入口，圖庫新增「石牌・談選擇」分類、原文全文搜尋、UTF-8原文下載與既有收藏／深連結支援。縮圖沿用原始石牌底圖；文字閱讀採橫排，保留原文、分行、空行、標點，不宣稱是原遊戲畫面截圖。原圖及3202動畫圖格不變。

重新擷取：`python3 asset_tools/add_steles.py`。`asset_tools/publish.py` 與 `integrate_guide.py` 已納入文字典藏；生成圖庫時保留現有 visitors.js 與 beacon。來源、地圖物件與SHA256記錄在 `web/collection/steles/source.json` 及 `manifest.json`。工作區同步 guide/collection 與 full_asset_pack，部署同步 web/collection。

原始封存檔SHA256核對，全部542筆素材路徑／動畫圖格可解析，四篇原文逐行核對；390px與1440px閱讀到底、搜尋、收藏重整、深連結、照片功能與首頁入口驗證通過。瀏覽器檢查：`asset_tools/test_steles.cjs`，傳入正式首頁URL可驗收線上版。報告 `verification/stele-local-checks.json`。本次只需部署Pages，沒有R2或Worker變更。


## 2026-09-09 石牌翻頁模式

依使用者要求，典藏石牌預設使用原始stele.png與Cubic_11.woff2呈現金色直排翻頁，保留橫排原文切換。網頁Canvas重現原版文字排版，不是遊戲截圖。分頁直接對照原始Fr類別paginate結果：之一2頁、之二2頁、之三5頁、之四5頁。左鍵下一頁、右鍵上一頁；觸控按鈕、放大捲動、模式切換保留頁次。網址新增page及view參數，舊asset網址仍有效。

共用實作在工作區asset_tools/stele-reader/，add_steles.py重新擷取時同步至full_asset_pack及guide/collection；integrate_guide.py同步該資料夾。字型來自原始素材包，沒有外部字型請求。部署資料夾為web/collection/stele-reader/。

測試asset_tools/test_stele_pages.cjs將每一篇每一頁與原始Fr分頁程式比較，並在390/1440px驗證邊界、方向鍵、模式與頁次保留、深連結重整、放大及照片回歸；test_steles.cjs保留原文搜尋／收藏測試。原版比對類別來自保留ASAR的dist/assets/index-BbZAngKC.js，自class Fr extends至class Rr extends前，暫存tmp/original-stele-class.js。報告verification/stele-pages-local-checks.json。


## 2026-09-09 完整主線攻略與流程圖

新增walkthrough/index.html：10個原版任務章節＋歸還錦囊／通關後兩節，共58步、152個對話截圖連結。逐步交代地點／人物、前置條件、操作、完成結果與卡關檢查。流程圖為可點選的HTML節點與連線，依条件分流和兩項皆須完成有明確標籤；第10章包含10名固定人物＋條件式楊教授的交談清單。步驟與清單勾選以localStorage canal-mainline-progress-v1獨立保存，不動遊戲存檔或舊圖鑑已讀進度。

Homepage hero、主要導覽、主線路書與每章概覽連到新頁；概覽任務同步為連續步驟，修正原第9章混入幽靈事件的摘要。原版只有10個任務章名，終章與通關後明確為另行整理。原圖鑑293事件與734截圖引用維持；GorDoN學生版仍排除。

內容來源：guide_tools/walkthrough_content.py；生成：python3 guide_tools/build_walkthrough.py。從保留的原始ASAR抽取場景方法，檢查每步對應method／rules／地圖觸發物件與公开event ID，輸出walkthrough/source.json與verification.json。此生成器會同步首頁guide-data.js的章節摘要，所以重新執行publish.py後應再執行build_walkthrough.py。前端CSS/JS在guide/walkthrough/；build_deploy_package.py已加入walkthrough資料夾複製。

驗證：Windows Node執行guide_tools/probe_walkthrough_gates.cjs，以原版方法隔離執行導演雙觸發、東翔雙舞步、解籤師傅、天珠與穿廟、夜店交談全員等門檻；UI／音訊／移動以替身取代，並非全程實玩。build_walkthrough.py會在tmp/mainline-source/生成此檢查需要的方法文字。guide_tools/test_walkthrough.cjs [BASE_URL]驗證390/1440px全12節與58節點、精確步驟深連結、分支文字、進度持久化與首頁入口。網站明確標示尚未完成從新遊戲到通關的全程實玩，不將程式規則核對當成實玩驗證。

新頁沿用visitors.js與Cloudflare beacon，圖片透過原圖鑑連結查看；不新增R2圖片，不更動Worker／D1。部署時同步guide/index.html、assets/app.js、assets/style.css、data/guide-data.js與walkthrough/至web/。檢查報告在verification/walkthrough-local-checks.json與walkthrough-gate-checks.json。


## 2026-09-09 攻略人物名稱查證

原始 app.asar.original 的 local_mj 顯示名稱為「在地MJ」；事件 eastXiang_nightclub_after（No.286）台詞為「好！我！西天翔！甘拜下風！」，已同時核對原始程式及 capture_masters/images/286-01.jpg。先前攻略把內部 eastXiang 譯成「東翔」有誤。第8、10章文字、流程圖與首頁章節資料統一改用「在地MJ」。重建驗證58步驟、152連結及所有來源引用通過；產出差異確認僅人物名稱替換，另更新首頁資料快取版本。

更正已上線：內容 commit `418d132`，Pages成功流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34309345250 ，正式站8.2與10.6名稱及全頁無「東翔」檢查通過。


## 2026-09-09 No.088 CD 架站位修正

使用者指出角色應更靠近CD架。原截圖captureObject視線間距把copy_cd站位從原始(140,280)往下推到(140,319)。capture_overrides.py改為此事件停用物件間距、保留原始互動格及walk_up；已用隔離原版引擎重擷取088-01並目視核對。僅此圖重新壓縮，其他733張manifest項目不變；原JPEG母檔有備份。查證紀錄verification/cd-position-checks.json。

已上線：內容commit `6f4cc17`，Pages流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34317988935 成功；遠端088-01 SHA及正式站瀏覽器1200px新圖載入通過。只新增1個R2物件，保留舊圖。


## 2026-09-09 歌詞頁遊戲字體與視覺更新

全頁統一Cubic_11遊戲字體，包括曲目、歌詞、表單、時間標記與頁尾；字型預載。米白曲目區搭配深綠歌詞閱讀區、暖金標題、CSS唱片裝飾與清楚的選中狀態；手機雙欄曲目、歌詞換行及桌面曲目捲動。資料與JS行為不變。320/390/768/1024/1440/1920px大字＋時間標記無溢出；12曲原文、搜尋深連結及閱讀設定持久化通過。測試guide_tools/test_lyrics_design.cjs，報告verification/lyrics-design-local-checks.json。只部署Pages，沿用字型及分析程式。

新版已上線：最終內容commit `d98fea3`，Pages流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34323834061 成功。正式站全頁遊戲字型載入、六種寬度大字及時間標記、原文與搜尋/設定回歸通過，報告verification/lyrics-design-live-checks.json。


## 2026-09-09 歌詞點陣CD與字體切換

依使用者要求移除黑膠裝飾，以pixel-cd.svg銀色點陣CD取代。閱讀工具列新增遊戲字體／一般字體：僅歌詞區與時間標記切換Cubic或系統無襯線字體，預設Cubic；localStorage canal-lyrics-font記住選擇。換曲／重新整理保留偏好，既有字級與時間開關獨立。測試guide_tools/test_lyrics_design.cjs擴充兩種字體的排版、原文不變、持久化與切回Cubic；本機通過，報告verification/lyrics-cd-font-local-checks.json。僅Pages更新。

已上線：內容commit `dc5548f`，Pages流程 https://github.com/wackyjazz/softlipa_canal/actions/runs/34325097916 成功。正式站CD載入、雙字體切換/記憶、手機/桌面排版與歌詞原文回歸通過，報告verification/lyrics-cd-font-live-checks.json。


## 2026-09-10 原生手機介面與過場截圖修正

原 capture_runtime.js 在每次事件把 ui.mobile 設為透明。改由 phone_policy.js 依原版流程設定手機持有／顯示狀態，再呼叫原生 UIScene.showMobile／hideMobile。使用原始 dist/ui/mobile.png、原位置(1180,30)、66×112、origin(1,0)及原後處理。取得前／拿取當句不顯示；open_mobile 起顯示且家中桌上手機消失。一般探索／對話顯示；after_chapter_1_end、after_chapter_3_end、last_talk 依原碼隱藏。可重複互動的初始家中物件沿用取得前場景，書櫃選用開過選單後的教學狀態。

292事件重擷取704張：656張顯示、48張依劇情隱藏。序章30張原圖及取樣資料未變；公開仍293事件734張，No275仍排除。原母檔及圖片備份 tmp/phone-recapture/before；新母檔 capture_masters/images。隨機路人／貓及動畫時點由原版生成，可與個別實玩不同。

同時核對歌曲後原始流程並修正022(聽完CD移到480,140看夜窗、恢復阿媽)、128(原生nightMask顯示)、137(橋邊對話仍是第9章夜間)。capture_overrides.py及events.json同步；不是重新套用全部舊override。

自檢：16組凍結同幀、只切換原生手機alpha的PNG像素比較，手機外差異皆0；原生取得手機trigger實測；3個歌曲後場景狀態及序章檢查；704張全圖／對話／手機區域壓縮PSNR各≥40dB。19張無法兼顧大小與門檻時保留JPEG，總計715 AVIF＋19 JPEG，734個獨立雜湊。740個內部文字／選項引用透過原渲染器核對原文及邊界。原入口、阿媽19張、038/039、088與序章取樣回歸檢查保留。

逐事件首圖縮圖目視，並抽查教學、夜景、CD架、输入框、夜店選項的原尺寸。這是來源核對＋原版引擎事件狀態重現，**不是新存檔全流程逐段實玩**，不可宣稱所有畫面與任意實玩逐像素相同。完整報告 guide/verification/phone-recapture.json、phone-source-evidence.json；本機比較頁 research/phone-recapture/index.html。

重建：audit_phone_source.py → build_capture.py → 啟動獨立tmp/guide_capture(9336) → capture_phone.cjs → probe_phone.cjs／review_phone.cjs → compress_phone.cjs → 完成實際目視校對後記錄manualReviewComplete → apply_phone_captures.py → publish.py → build_phone_review.py。分階段輸出在tmp/phone-recapture，不先覆蓋正式圖。再執行verify.py、verify_capture_fixes.py、verify_compression.cjs、test_site.cjs。

測試工具修正：CDP忽略Edge自行打開的Rewards內部頁；test_site開跑清除隔離測試筆記，Gina預期只命中可達的No274一筆。使用本次啟動的擷取程序11368已精確結束，沒有操作使用者其他遊戲。

正式上線：內容commit93f9f64；Pages34447375557成功；Worker ea53fed7-296f-4d8a-8199-e2121755bec4。702新物件／32沿用，19個正式GET內容核對通過。兩份ZIP已重建逐檔驗證。
