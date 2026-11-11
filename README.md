# NOVA Protocol — 失落基地

> **支援 1～4 人彈性合作、小五至國二混齡教學、三層關卡難度（基礎／標準／挑戰）與教師端學習歷程管理的 2D 科幻像素風網頁程式教育遊戲。**

---

## 一、專案特色與教學設計

1. **零基礎友善入口（指令卡 ➔ Google Blockly ➔ Python 對照）**
   - 第一階段提供直覺的「指令卡／動作卡」排列介面，先讓學生理解「指令」與「由上而下執行順序」。
   - 可一鍵將指令卡無縫轉換為 **Google Blockly** 積木，並可開啟即時 **Python 語法並排對照預覽**。
   - 尚未解鎖的後續章節積木以「🔒 鎖定預覽」方式呈現，避免初學者資訊過載。
2. **七大章節 × 三層難度（共 36 個可玩關卡變體）**
   - **第一章：新手維修區**（指令與執行順序：5 關 × 3 難度）
   - **第二章：能源研究區**（固定次數與條件迴圈：2 關 × 3 難度）
   - **第三章：故障迷宮**（條件判斷 `if` / `if-else` 與障礙感測：1 關 × 3 難度）
   - **第四章：資源管理中心**（變數 `energy` 狀態追蹤與比較運算：1 關 × 3 難度）
   - **第五章：雙人控制實驗室**（布林邏輯 `AND` / `OR` / `NOT` 與單人等價脈衝排程機制：1 關 × 3 難度）
   - **第六章：自動化工廠**（自訂函式 `def` / `call` 與模組化重用：1 關 × 3 難度）
   - **最終章：NOVA 核心**（開放式多路線、多解法綜合基地修復任務：1 關 × 3 難度）
   - 每關皆具備 **基礎（Guided）**、**標準（Core）**、**挑戰（Challenge）** 三種實質不同的地圖配置、條件限制與提示深度，且不依年級限制學生選擇。
3. **1～4 人彈性合作與單人等價流程**
   - **1 人**：完整單人遊玩所有主線章節；第 5 章雙開關關卡內建「單人脈衝鎖定保持」等價機制，不需等待其他玩家。
   - **2～4 人**：透過 6 碼房間代碼加入，系統依實際人數動態分配角色（程式編排、地圖分析、執行測試、邏輯除錯），採用「單一主要編輯權」並於每關完成後自動輪替操作權。
   - 支援中途加入（先以觀察員身分加入，下一關納入輪替）與斷線自動移交操作權；人數降至 1 人時自動無縫轉回單人模式。
   - 僅提供預設正向快捷訊息與表情符號，不設公開聊天室或陌生人配對。
4. **安全執行虛擬機（禁止 `eval` / `exec`）與伺服器端權威驗證**
   - 前後端共用結構化 AST 指令虛擬機，嚴格限制最大積木數（200）、最大迴圈次數（100）、最大步數（500）與最大巢狀深度（6）。
   - 支援 **執行、暫停、繼續、單步執行、重新開始、4 段速度調整（0.5x～4.0x）**、執行積木高亮與友善除錯提示。
   - 通關判定由 FastAPI 後端 `engine_validator.py` 實際模擬驗證，不單靠前端判斷。
5. **教師端／課堂教學管理中心**
   - 支援建立與關閉課堂教學場次（產生 `CLS-XXXXX` 場次代碼）、檢視學生匿名代號進度、閱讀由實際學習事件產生的**教師可讀證據摘要**、手動指派關卡與三層難度、查看多人房間操作權輪替紀錄，以及匯出不含個資之匿名 JSON 課堂摘要。

---

## 二、技術架構與資料夾結構

- **前端 (`frontend/`)**：HTML5、CSS3、JavaScript (ES Modules)、Vite 6、Phaser 3.87、Google Blockly 11
- **後端 (`backend/`)**：Python 3.12+、FastAPI、WebSocket、SQLAlchemy 2.0、Pydantic v2
- **資料庫**：PostgreSQL（正式環境使用 Render PostgreSQL；本機開發若未設定外部 `DATABASE_URL`，自動透過 `pgserver` 啟動真實的使用者空間內嵌 PostgreSQL 伺服器）

```text
AI WEB-GAME/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、CORS 與生命週期初始化
│   │   ├── config.py            # 環境變數與安全限制設定
│   │   ├── database.py          # SQLAlchemy + PostgreSQL 連線管理
│   │   ├── models.py            # 15 張核心資料表 ORM 定義
│   │   ├── schemas.py           # Pydantic 請求與回應綱要
│   │   ├── seed.py              # 7 章節 × 3 難度關卡與 10 項成就種子資料
│   │   ├── engine_validator.py  # 後端安全 AST 執行模擬與通關驗證引擎
│   │   ├── adaptive.py          # 學習事件分析、保守型難度推薦與教師可讀摘要
│   │   ├── ws_manager.py        # WebSocket 1~4 人房間同步、輪替與斷線移交
│   │   └── routers/             # players, levels, rooms, teacher API 路由
│   ├── tests/
│   │   └── test_api_and_engine.py # 自動化測試套件
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js              # 前端主控制器
│       ├── style.css            # 科幻像素風響應式介面樣式
│       ├── services/            # api.js, ws.js, audio.js (Web Audio 合成器)
│       ├── data/                # levelsData.js (機體塗裝、配件、積木圖鑑)
│       ├── game/                # PixelAssets.js, GameScene.js, Interpreter.js
│       ├── editor/              # ActionCardEditor.js, BlocklySetup.js, PythonGenerator.js
│       └── ui/                  # UIManager.js, TeacherPanel.js
├── .env.example
├── render.yaml
└── README.md
```

---

## 三、本機啟動方式

### 1. 環境變數設定（選填）

複製 `.env.example` 為 `.env`：

```bash
cp .env.example .env
```

- 預設教師通行密鑰為：`NOVA-TEACHER-2026`（可透過環境變數 `TEACHER_PASSKEY` 修改）。
- 若未填寫 `DATABASE_URL`，後端啟動時會自動透過 `pgserver` 建立並啟動本機 PostgreSQL 資料庫。

### 2. 啟動後端 (FastAPI + PostgreSQL)

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

後端 API 將運行於 `http://127.0.0.1:8000`（健康檢查：`GET /api/health`）。

### 3. 啟動前端 (Vite + Phaser 3 + Blockly)

開啟另一個終端機視窗：

```bash
cd frontend
npm install
npm run dev
```

開啟瀏覽器前往 `http://localhost:5173/` 即可開始遊玩！

---

## 四、如何執行測試與驗收

### 1. 後端與安全執行引擎自動化測試

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -v
```

測試涵蓋：
- PostgreSQL 15 張資料表與 12 關 × 3 層難度種子資料完整性。
- 單人完整流程、工作區版本化儲存與載入、錯誤後自行修正 (`self_corrected`) 與成就解鎖。
- 全 7 章節代表關卡與第 5 章雙人控制實驗室之「單人等價脈衝排程解法」驗證。
- 1～4 人房間建立、加入、滿員拒絕第 5 人、非主操作者禁止提交、過關自動輪替操作權、WebSocket 即時同步與斷線自動移交。
- 教師端登入、建立場次、學生代號加入、指派任務與跨教師場次權限隔離（HTTP 403）。
- 惡意過量迴圈與指令數之安全阻擋。

### 2. 前端正式建置測試

```bash
cd frontend
npm run build
```

---

## 五、GitHub 與 Render 部署指南

本專案已提供 [`render.yaml`](file:///run/media/chaichai/DATA/Linux/%E6%96%87%E4%BB%B6/AI%20WEB-GAME/render.yaml) Blueprint，可一鍵部署至 Render：

1. 將本專案推送至 GitHub 儲存庫。
2. 登入 Render，選擇 **New ➔ Blueprint**，連結該 GitHub 儲存庫。
3. Render 會自動建立：
   - **`nova-protocol-db` (PostgreSQL)**：永久儲存玩家進度、房間、學習事件與教學場次資料（不依賴本機檔案系統）。
   - **`nova-protocol-backend` (Web Service)**：部署 FastAPI 與 WebSocket 服務，自動注入 `DATABASE_URL`。請在環境變數設定 `TEACHER_PASSKEY` 與前端的 `CORS_ORIGINS`（例如 `https://nova-protocol-frontend.onrender.com`）。
   - **`nova-protocol-frontend` (Static Site)**：執行 `npm install && npm run build` 並發布 `dist/`。請設定環境變數：
     - `VITE_API_URL=https://<你的後端網址>.onrender.com`
     - `VITE_WS_URL=wss://<你的後端網址>.onrender.com`

---

## 六、資料庫維運、錯誤紀錄與場次過期策略

1. **資料庫備份與跨版本遷移相容性**
   - 永久資料全部保存在 PostgreSQL 中，啟動時 `seed_database()` 採冪等更新（Idempotent Upsert），部署新版本或更新關卡文字時不會清除或破壞既有玩家的 `players`、`player_progress` 與 `player_achievements` 紀錄。
   - Blockly 與指令卡工作區序列化 JSON 內含 `"version": 1` 欄位，確保未來擴充自訂積木時具備向下相容能力。
   - 建議在 Render PostgreSQL 開啟每日自動快照備份，或定期透過 `pg_dump $DATABASE_URL > backup.sql` 備份。
2. **場次生命週期與資料最小化原則**
   - 教學場次 (`teaching_sessions`) 預設有效期限為 24 小時（教師可手動關閉或延長）；過期後自動轉為 `expired` 狀態並停止接受新成員加入。
   - `learning_events` 僅記錄結構化學習事件（如概念接觸、錯誤類別代碼、提示層級、是否自行修正），不記錄任何敏感文字或個人隱私資訊。
3. **錯誤紀錄與安全防護**
   - 後端對所有房間操作、任務提交與教師端查詢皆實施伺服器端權限驗證（HTTP 401/403），且 WebSocket 連線強制驗證房間成員資格（非成員以代碼 `4003` 拒絕）。

