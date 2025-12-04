# NCU 課程篩選器後端

## 安裝步驟

1. 安裝 Python 依賴：
```bash
pip install -r requirements.txt
```

## 啟動服務器

```bash
python app.py
```

服務器將在 `http://localhost:3000` 運行

## API 端點

### 1. 篩選課程
- **URL**: `/api/filter-courses`
- **Method**: `POST`
- **Request Body**:
```json
{
  "department": "資工系",
  "grade": 1,
  "busyTimes": ["1-2", "1-3", "3-5"]
}
```
- **Response**:
```json
{
  "success": true,
  "count": 50,
  "courses": [...]
}
```

### 2. 取得所有課程
- **URL**: `/api/courses`
- **Method**: `GET`

### 3. 健康檢查
- **URL**: `/api/health`
- **Method**: `GET`