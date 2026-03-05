"""
FootballBet API - 從香港賽馬會足智彩抓取足球賽事資料
專注讓球盤 (Asian Handicap)
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pytz

# 設定時區
HKT = pytz.timezone('Asia/Hong_Kong')

app = FastAPI(
    title="FootballBet API",
    description="從香港賽馬會足智彩抓取足球賽事資料 - 讓球盤",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Models ============

class Match(BaseModel):
    """賽事模型"""
    fb_code: str
    hkt_time: str
    home_team: str
    away_team: str
    handicap_line: float  # 讓球線，如 -1, -1.5, +1 等
    home_odds: float      # 主讓赔率
    away_odds: float      # 客受赔率
    status: str           # 未開波 / 進行中 / 已完結
    value_rating: str     # 高價值 / 一般

class Recommendation(BaseModel):
    """推介模型"""
    bet_number: int
    selection: str
    stake: float
    odds: float
    potential_return: float
    reason: str

# ============ 模擬數據 ============

def get_mock_matches() -> List[Match]:
    """產生模擬數據用於測試"""
    now = datetime.now(HKT)
    
    mock_matches = [
        # 2026-03-05 賽事
        Match(
            fb_code="FB4875",
            hkt_time="2026-03-05 03:30",
            home_team="曼城",
            away_team="諾定咸森林",
            handicap_line=-1.5,
            home_odds=2.15,
            away_odds=1.75,
            status="未開波",
            value_rating="高價值"
        ),
        Match(
            fb_code="FB4873",
            hkt_time="2026-03-05 03:30",
            home_team="白禮頓",
            away_team="阿仙奴",
            handicap_line=+1.0,
            home_odds=2.17,
            away_odds=1.70,
            status="未開波",
            value_rating="高價值"
        ),
        Match(
            fb_code="FB4942",
            hkt_time="2026-03-05 05:00",
            home_team="巴西女足",
            away_team="委內瑞拉女足",
            handicap_line=-2.0,
            home_odds=2.00,
            away_odds=1.85,
            status="未開波",
            value_rating="高價值"
        ),
        Match(
            fb_code="FB4941",
            hkt_time="2026-03-05 04:30",
            home_team="阿根廷女足",
            away_team="哥倫比亞女足",
            handicap_line=+1.0,
            home_odds=2.00,
            away_odds=1.82,
            status="未開波",
            value_rating="高價值"
        ),
        Match(
            fb_code="FB4895",
            hkt_time="2026-03-05 03:00",
            home_team="阿爾克馬爾",
            away_team="泰斯達",
            handicap_line=-1.5,
            home_odds=2.15,
            away_odds=1.72,
            status="未開波",
            value_rating="高價值"
        ),
        Match(
            fb_code="FB4870",
            hkt_time="2026-03-05 04:15",
            home_team="紐卡素",
            away_team="曼聯",
            handicap_line=0,
            home_odds=1.95,
            away_odds=1.95,
            status="未開波",
            value_rating="一般"
        ),
        Match(
            fb_code="FB4936",
            hkt_time="2026-03-05 17:00",
            home_team="澳洲女足",
            away_team="伊朗女足",
            handicap_line=-4.5,
            home_odds=1.95,
            away_odds=1.90,
            status="未開波",
            value_rating="高價值"
        ),
        # 已完結既賽事（應該被過濾）
        Match(
            fb_code="FB4868",
            hkt_time="2026-03-04 17:30",
            home_team="SC相模原",
            away_team="群馬草津溫泉",
            handicap_line=-1.0,
            home_odds=1.85,
            away_odds=2.00,
            status="已完結",
            value_rating="一般"
        ),
    ]
    
    return mock_matches

# ============ Scraping Functions ============

async def scrape_hkjc_matches(
    date: str,
    min_handicap: float = -2,
    max_handicap: float = 2,
    status_filter: str = None
) -> List[Match]:
    """
    從 HKJC 抓取讓球盤數據
    
    注意: HKJC 有防爬機制，實際使用需要:
    1. Selenium 模擬瀏覽器
    2. 或使用官方 API (如有)
    3. 或 Proxy + 延遲
    
    呢度先用模擬數據
    """
    # 檢查是否使用模擬數據
    use_mock = os.getenv("MOCK_DATA", "true").lower() == "true"
    
    if use_mock:
        return get_mock_matches()
    
    # TODO: 實現真實爬蟲
    # 需要 Selenium + Chrome headless
    raise HTTPException(
        status_code=501,
        detail="真實爬蟲功能待實現，請設置 MOCK_DATA=true 使用模擬數據"
    )

# ============ Endpoints ============

@app.get("/", tags=["Root"])
async def root():
    """API 根路徑"""
    return {
        "name": "FootballBet API",
        "version": "1.0.0",
        "description": "香港賽馬會足智彩 - 讓球盤資料API"
    }

@app.get("/health", tags=["Health"])
async def health():
    """健康檢查"""
    return {
        "status": "healthy",
        "timezone": "Asia/Hong_Kong",
        "time": datetime.now(HKT).isoformat()
    }

@app.get("/matches", response_model=List[Match], tags=["Matches"])
async def get_matches(
    date: str = Query(
        default=None,
        description="日期 (YYYY-MM-DD)，預設今日"
    ),
    min_handicap: float = Query(
        default=-2,
        description="最小讓球線 (-2)"
    ),
    max_handicap: float = Query(
        default=2,
        description="最大讓球線 (2)"
    ),
    status: str = Query(
        default=None,
        description="狀態篩選: 未開波 / 進行中"
    )
):
    """
    獲取讓球盤賽事列表
    
    - **date**: 日期 (YYYY-MM-DD)
    - **min_handicap**: 最小讓球線 (如 -2)
    - **max_handicap**: 最大讓球線 (如 2)  
    - **status**: 狀態 (未開波 / 進行中)
    """
    # 處理日期
    if not date:
        date = datetime.now(HKT).strftime("%Y-%m-%d")
    
    # 驗證日期格式
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式錯誤，請使用 YYYY-MM-DD")
    
    # 驗證讓球線範圍
    if min_handicap > max_handicap:
        raise HTTPException(status_code=400, detail="min_handicap 不能大於 max_handicap")
    
    # 獲取數據
    try:
        matches = await scrape_hkjc_matches(date, min_handicap, max_handicap, status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取數據失敗: {str(e)}")
    
    # 過濾結果
    filtered = []
    for m in matches:
        # 篩選狀態
        if status and m.status != status:
            continue
        
        # 篩選讓球線範圍
        if m.handicap_line < min_handicap or m.handicap_line > max_handicap:
            continue
        
        filtered.append(m)
    
    return filtered

@app.get("/recommend", response_model=List[Recommendation], tags=["Recommend"])
async def get_recommendations():
    """
    投注推介
    
    根據 600 蚊本金，建議 3 注每注 200 蚊。
    優先選擇 ±2 球內高價值讓球。
    """
    # 獲取所有未開波既高價值賽事
    try:
        all_matches = await scrape_hkjc_matches(
            datetime.now(HKT).strftime("%Y-%m-%d"),
            min_handicap=-2,
            max_handicap=2,
            status_filter="未開波"
        )
    except HTTPException:
        all_matches = get_mock_matches()
    
    # 篩選高價值 + 讓球線範圍內
    candidates = [
        m for m in all_matches 
        if m.value_rating == "高價值" 
        and -2 <= m.handicap_line <= 2
        and m.status == "未開波"
    ]
    
    # 選擇最高價值既 3 個
    # 排序: 先按赔率高，再按讓球線（中間既較穩）
    candidates.sort(key=lambda x: (-x.home_odds, abs(x.handicap_line)))
    selected = candidates[:3]
    
    # 如果唔夠 3 個，放寬條件
    if len(selected) < 3:
        others = [
            m for m in all_matches 
            if m not in selected and m.status == "未開波"
        ]
        others.sort(key=lambda x: -x.home_odds)
        selected.extend(others[:3-len(selected)])
    
    # 生成推介
    recommendations = []
    stake = 200.00
    
    for i, match in enumerate(selected[:3], 1):
        potential = stake * match.home_odds
        reason = f"{match.home_team} 讓 {abs(match.handicap_line)} 球"
        if match.handicap_line > 0:
            reason = f"{match.away_team} 受 {match.handicap_line} 球"
        
        recommendations.append(Recommendation(
            bet_number=i,
            selection=f"{match.home_team} vs {match.away_team} ({match.home_odds})",
            stake=stake,
            odds=match.home_odds,
            potential_return=round(potential, 2),
            reason=reason
        ))
    
    return recommendations

# ============ 錯誤處理 ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": "服務器內部錯誤",
        "detail": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
