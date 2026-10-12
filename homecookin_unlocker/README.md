# 家常音樂彩蛋解鎖工具 v0.2 桌面版

保留原版遊戲內容，對符合條件的存檔只將 `isMember` 從 `false` 改成 `true`。謎之男子的登場、對話、道具與任務仍由原版第四章流程處理。這是一次性的本機存檔工具，不需官網帳密，也不會發送網路請求。

## 一般玩家：直接使用桌面版

Windows 下載 `HomeCookinUnlocker-Windows-x64.zip`，解壓縮後雙擊 `HomeCookinUnlocker.exe`。桌面版內含所需執行環境，**不需要安裝 Python、不需要輸入指令**。

Mac 下載對應的 `HomeCookinUnlocker-macOS-arm64.zip`（Apple Silicon：M1 / M2 / M3 等）或 `HomeCookinUnlocker-macOS-x64.zip`（Intel），解壓縮後將 `HomeCookinUnlocker.app` 拖入「應用程式」，再雙擊開啟。可在蘋果選單的「關於這台 Mac」查看晶片／處理器種類。

Mac 測試版未使用 Developer ID 憑證簽署，也未經 Apple 公證。若首次開啟顯示無法驗證開發者或無法檢查 App，可依 [Apple 的操作說明](https://support.apple.com/zh-tw/102445)，在嘗試開啟後前往「系統設定 → 隱私權與安全性 → 強制打開」。此操作只針對你確認來源的這個 App，不需關閉整個系統的安全保護。

1. 程式自動尋找存檔；有需要才按「選擇存檔」。
2. 確認顯示「這份存檔可以解鎖」，完全關閉遊戲。
3. 勾選「我已完全關閉遊戲」，按「備份並開啟彩蛋資格」。
4. 完成後關閉工具，回到遊戲選擇「繼續遊戲」。

「還原備份」會列出可驗證的備份時間、章節與資格狀態，不用手動輸入資料夾路徑。還原前會明確提示整份進度回到備份時間。

| 版本 | 狀態 |
| --- | --- |
| Windows x64 EXE | 已產生免安裝桌面測試版；尚未使用發行者憑證簽署 |
| Mac Apple Silicon APP | 已在 GitHub macOS 15 arm64 環境建置，通過 24 項測試、原生 GUI 解鎖／還原與封裝 APP 啟動檢查 |
| Mac Intel APP | 已在 GitHub macOS 15 Intel 環境建置，通過 24 項測試、原生 GUI 解鎖／還原與封裝 APP 啟動檢查 |

一般玩家應拿到對應平台的應用程式包，下面的 Python / CLI 指令是給開發者使用。Mac 包內已有 APP 與執行環境；不要把來源碼 ZIP 當作安裝包。

Mac 建置紀錄：[GitHub Actions #38209474072](https://github.com/wackyjazz/softlipa_canal/actions/runs/38209474072)，原始碼 commit `f74ac5fc849d5ed4280f3dc7c554c444638edd82`。使用獨立的 `build/homecookin-macos-20261012` 分支，沒有修改既有網站主分支或部署網站。

## 桌面版設計

- 使用 Tk 桌面 UI，與已驗證的存檔核心共用邏輯。
- 主畫面只顯示玩家能理解的狀態，旗標名稱與版本細節放在「查看詳情」。
- 未找到、無法驗證、進度已分岔、已開啟、已觸發事件都有不同狀態；只有符合條件且確認關閉遊戲後才能解鎖。
- 備份及檢查在背景工作執行，不凍結視窗；操作中不能關閉視窗或重複按下操作。
- 對畫面檢查的存檔建立 SHA-256 快照，按下解鎖／還原時若存檔已改變，要求重新檢查。
- 支援 Windows DPI 縮放；小螢幕可捲動查看完整介面。程序檢查不跳出 PowerShell 黑色視窗。

## 桌面版建置與發佈（開發者）

須在目標作業系統使用 Python 3.13 與 Tk 建置：

```sh
python -m pip install -r homecookin_unlocker/requirements-build.txt
python homecookin_unlocker/build_desktop.py --output desktop-build
```

Windows 產出單一無主控台 EXE；macOS 產出含執行環境的 APP。ZIP 只放應用程式、簡短使用說明和建置資訊，不把 Python 腳本當作玩家入口。

專案的 `.github/workflows/homecookin-desktop.yml` 提供手動觸發的三平台建置；本次使用 `.github/workflows/homecookin-macos.yml` 在獨立建置分支完成兩種 Mac 原生架構的測試及打包。macOS 產物帶有打包工具的 ad-hoc 簽章，通過 `codesign --verify --deep --strict`；這不等於 Developer ID 簽署或 Apple 公證。

正式發佈還需要：

- Windows：使用發行者的程式碼簽章憑證簽署 EXE，再重新封裝及計算雜湊。未簽署測試包可能被下載保護提示；簽章也不保證立即建立 SmartScreen 信譽。
- Mac：在已安裝 Developer ID 憑證的建置環境設定 `MAC_CODESIGN_IDENTITY` 後建置，再提交 Apple 公證、驗證及附加公證票證後重新封裝。目前未加入任何憑證或帳密，未執行公證。
- 使用實際遊戲存檔，在兩平台驗收第四章彩蛋完整流程。自動化測試只使用合成存檔。

參考：[PyInstaller 的平台建置限制](https://pyinstaller.org/en/stable/)、[Apple 公證流程](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)、[GitHub 原生建置環境](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)。

## 支援範圍

- 依專案中的 Windows 原版 **1.0.0** 程式分析，支援 `CLSAVE2` 格式的 `save.dat`。
- 這個格式標記不是遊戲版本號；工具不宣稱能辨識所有新版本。會檢查 HMAC、壓縮格式與必要欄位，不符合即停止。
- Windows / Mac 共用 Python 標準函式庫核心；開發者直接執行 CLI 時需 **Python 3.9 以上**，無第三方套件。桌面建置環境使用 Python 3.13；打包後的玩家版本不需要 Python。
- Mac 版已在原生 macOS 15 測試合成存檔及桌面操作。**實際 Mac 原版遊戲存檔、兩平台遊戲內彩蛋流程與更舊 macOS 版本仍待驗證。** Mac 預設存檔路徑依遊戲跨平台主程序推導。
- 不支援直接編輯舊版 `save.json`；請先讓原遊戲讀取並存成 `save.dat`。

## 命令列核心使用方式（開發者）

1. 沒有存檔時，先在原遊戲跳過登入，開始遊戲並確認已存檔。
2. 完全關閉遊戲。
3. Windows 開啟 `Unlock.cmd`；Mac 開啟 `Unlock.command`。若 Mac 沒有保留執行權限，可在此目錄用 `bash Unlock.command` 啟動。
4. 選擇「檢查存檔」或「解鎖資格」。解鎖前會顯示路徑、章節、資格與預計變更，並請你確認遊戲已關閉。
5. 啟動遊戲，選擇**繼續遊戲**。第四章仍須向唱片行詢問《家常音樂》，並回到台南街道，依原版條件觸發彩蛋。

新遊戲會建立新的資格狀態，須重新執行工具。已解鎖的存檔再次執行不會重複寫入或建立備份。

預設路徑：

| 平台 | 存檔 |
| --- | --- |
| Windows | `%APPDATA%\canal-legend\gameData\save.dat` |
| Mac（待實機確認） | `~/Library/Application Support/canal-legend/gameData/save.dat` |

工具不會掃描其他使用者，也不會自動選到 GorDoN 試玩版存檔。自訂路徑請使用 `--save`。

```sh
python3 unlock.py status --save "/完整路徑/save.dat"
python3 unlock.py unlock --save "/完整路徑/save.dat" --game-closed
python3 unlock.py restore --save "/完整路徑/save.dat" --backup "/完整路徑/備份資料夾" --game-closed
```

Windows 可把 `python3` 換成 `py -3`。`status` 只讀取；寫入必須先關閉遊戲。

## 哪些進度可以處理

| 存檔狀態 | 行為 |
| --- | --- |
| 第 0–3 章，沒有相關分支或完成紀錄 | 只改 `isMember` |
| 第 4 章，尚未進入尋找／老人分支 | 只改 `isMember`，保留是否已向唱片行詢問的進度 |
| 同上，`isMember` 已為 true | 不寫入 |
| 已有 `find_home_cookin`、`ask_old_man_home_cookin` 或 `ask_home_cookin_repeat_again` | 停止，建議使用分支前存檔 |
| 已取得 `home-cookin`、已有 `old_man_talk_home_cookin` | 停止，不重設道具或老人分支 |
| 已有 `time_traveler`、`complete`，或超過第四章 | 停止，不提供重播或倒退章節 |

其中 `ask_old_man_home_cookin` 影響原版任務編號；不能為了生成 NPC 就任意清除。第一版不新增任何事件旗標、不直接發放道具、不修改章節。遇到保守拒絕的存檔，先個別分析其分支，不提供 `--force`。

## 備份與寫入設計

1. 檢查存檔格式、HMAC-SHA256 與劇情條件。
2. 取得此工具的排他鎖；確認遊戲程序未被偵測到，且沒有 `save.dat.tmp`。
3. 於存檔旁的 `homecookin-backups/<時間-識別碼>/` 備份完整原始位元組，附上目標路徑、SHA-256 與操作紀錄。
4. 解碼、只更動 `isMember`、重新 gzip / HMAC，驗證其他欄位值完全相同。
5. 在同目錄寫入暫存檔、flush / fsync，重新檢查原存檔沒變，再以原子替換方式寫入並讀回驗證。

程式不修改遊戲 EXE、App、ASAR，也不需要系統管理員權限。存檔的壓縮位元組會改變，但解碼後除 `isMember` 外的欄位值保持一致；原始位元組保留於備份。

程序名稱檢查是額外保護，無法辨識所有改名執行檔；務必自行完全關閉遊戲，操作期間不要啟動。工具鎖只能排除其他解鎖工具，不能鎖住原遊戲。若工具曾異常結束留下 `.homecookin.lock`，確認所有工具均已關閉後才手動移除鎖定檔。

還原須指定由此工具為**相同完整路徑**建立的備份資料夾；會驗證雜湊及內容，並先備份目前存檔。**還原整份備份會回到當時進度，包含後來取得的道具與任務。** 不會自動執行還原，也不會默默挑選最新備份。

## 開發驗證

在專案根目錄執行：

```sh
python3 -m unittest discover -s homecookin_unlocker/tests -v
```

測試使用臨時合成存檔，涵蓋解鎖、原始備份、還原、拒絕不適用進度、損毀與並行寫入。另有原遊戲 JavaScript 編解碼函式的交叉驗證腳本，使用本機原始 ASAR 擷取函式後在 Node.js 執行；不啟動遊戲、不接觸玩家存檔。

驗證結果：24 項自動測試在 WSL、macOS arm64、macOS Intel 通過，包含桌面狀態與操作前快照保護；三平台原生 Tk 視窗以合成存檔驗證按鈕狀態、解鎖、備份清單與還原。打包後的 Windows EXE 與兩種 Mac APP 均在移除建置用 Python 環境的子程序設定中成功啟動，啟動沒有修改測試存檔。Mac APP 的封裝簽章也通過驗證。原版 JavaScript 函式在 Windows Node.js 25.5.0 成功解碼 Python 產生的合成存檔，並確認只有 `isMember` 改變；原版函式產生的存檔也通過 Python 解碼。以上仍不代表完成原遊戲內彩蛋驗收。

在有原始 ASAR 的專案目錄可重跑交叉驗證：

```sh
python3 homecookin_unlocker/tests/compatibility_check.py prepare
node tmp/homecookin-compat/check.cjs
python3 homecookin_unlocker/tests/compatibility_check.py verify
```

發佈前仍需在 Windows、Mac 各驗證：關閉遊戲後解鎖早期存檔、遊戲正常讀取、第四章謎之男子完整登場與贈送道具、存檔重開、備份還原，以及已走老人分支時的拒絕提示。

原始依據：`electron/main.cjs` 的存檔編解碼、`loading.checkSave` 的資格讀取，以及 `tmp/mainline-source/` 內的 `tainan--setupChapter4.txt`、`tainan--buildEventRules.txt`、`tainan--triggerHomeCookinEvent.txt`、`platform--getPlaySongMissionNumber.txt`。
