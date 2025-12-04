# 部署指南

## 前端部署到 Vercel

### 1. 準備前端文件
確保 `frontend` 資料夾包含以下文件：
- `index.html`
- `script.js`
- `style.css`
- `config.js`

### 2. 部署到 Vercel

1. 前往 [Vercel](https://vercel.com/) 註冊並登入
2. 點擊 "Add New" → "Project"
3. 導入你的 GitHub 儲存庫（或直接上傳 frontend 資料夾）
4. 設定如下：
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: 留空（靜態網站不需要建置）
   - **Output Directory**: `./`（當前目錄）
5. 點擊 "Deploy"

### 3. 部署後更新 config.js

部署完成後，你會得到一個 Vercel URL（例如：`https://your-app.vercel.app`）

**重要**: 需要更新兩個地方的配置：

1. 更新 `frontend/config.js` 中的生產環境 URL：
```javascript
const API_CONFIG = {
    development: 'http://localhost:3000',
    production: 'https://your-render-backend.onrender.com'  // 改成你的 Render URL
};
```

2. 重新部署前端（Vercel 會自動偵測 Git 更新）

---

## 後端部署到 Render

### 1. 準備後端文件
確保 `backend` 資料夾包含：
- `app.py`
- `requirements.txt`
- `output.csv`（課程數據）
- `bigcontent.xlsx`（完整課程資料）

### 2. 部署到 Render

1. 前往 [Render](https://render.com/) 註冊並登入
2. 點擊 "New +" → "Web Service"
3. 連接你的 GitHub 儲存庫
4. 設定如下：
   - **Name**: 自訂名稱（例如：ncu-course-filter）
   - **Region**: Singapore（或其他離台灣近的）
   - **Branch**: main
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. 設定環境變數（Environment Variables）：
   - `FRONTEND_URL`: `https://your-app.vercel.app`（你的 Vercel 前端 URL）
   - `FLASK_ENV`: `production`
   - `PORT`: 留空（Render 會自動設定）

6. 點擊 "Create Web Service"

### 3. 部署完成後

1. 複製 Render 給你的 URL（例如：`https://your-app.onrender.com`）
2. 回到前端的 `config.js`，更新 `production` URL
3. 推送更新到 GitHub，Vercel 會自動重新部署

---

## 測試部署

### 測試後端
訪問 `https://your-render-backend.onrender.com/api/health`
應該看到：
```json
{
  "status": "ok",
  "courses_loaded": 1474
}
```

### 測試前端
1. 訪問你的 Vercel URL
2. 輸入系所和年級
3. 選擇忙碌時段
4. 點擊「開始篩選」
5. 應該能看到課程列表

### 測試下載功能
1. 勾選幾門課程
2. 點擊「下載選中課程」
3. 應該能下載 Excel 檔案

---

## 環境變數總覽

### 前端 (config.js)
```javascript
const API_CONFIG = {
    development: 'http://localhost:3000',
    production: 'https://your-render-backend.onrender.com'
};
```

### 後端 (Render 環境變數)
- `FRONTEND_URL`: Vercel 前端 URL（用於 CORS）
- `FLASK_ENV`: `production`
- `PORT`: 自動設定（不需手動填）

---

## 常見問題

### 1. CORS 錯誤
確保 Render 的 `FRONTEND_URL` 環境變數設定正確，包含完整的 `https://` 前綴

### 2. 課程數據沒有載入
檢查 Render 部署日誌，確認 `output.csv` 和 `bigcontent.xlsx` 檔案已正確上傳

### 3. 下載功能失敗
檢查 Render 日誌，確認 `bigcontent.xlsx` 檔案存在且可讀取

### 4. Render 免費版限制
- 免費版會在閒置 15 分鐘後休眠
- 首次訪問會需要等待約 30 秒喚醒
- 建議使用 [UptimeRobot](https://uptimerobot.com/) 定期 ping 保持喚醒

---

## 更新部署

### 更新前端
推送更改到 GitHub → Vercel 自動重新部署

### 更新後端
推送更改到 GitHub → Render 自動重新部署

### 更新課程數據
1. 更新 `output.csv` 或 `bigcontent.xlsx`
2. 推送到 GitHub
3. Render 會自動重新部署並載入新數據