# FootballBet API

從香港賽馬會足智彩 (bet.hkjc.com) 抓取足球賽事資料，專注讓球盤 (Asian Handicap)。

## 功能

- 獲取讓球盤數據
- 篩選未開波/進行中賽事
- 價值評級
- 投注推介

## 安裝

```bash
pip install -r requirements.txt
```

## 運行

```bash
# 開發模式
uvicorn main:app --reload

# 生產模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /matches
獲取讓球盤賽事列表

參數:
- `date` (YYYY-MM-DD, 預設今日)
- `min_handicap` (預設 -2)
- `max_handicap` (預設 2)
- `status` (未開波 / 進行中)

### GET /recommend
根據 600 蚊本金推介 3 注每注 200 蚊

### GET /health
健康檢查

## 使用模擬數據

```bash
MOCK_DATA=true uvicorn main:app --reload
```
