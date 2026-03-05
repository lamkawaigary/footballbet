"""
HKJC Selenium Scraper - 從香港賽馬會足智彩抓取讓球盤數據
"""
import os
import time
import random
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

HKT = pytz.timezone('Asia/Hong_Kong')


def create_driver():
    """建立 Chrome headless 瀏覽器"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    # 防止被偵測為 bot
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error installing chromedriver: {e}")
        # Try with system chromedriver
        driver = webdriver.Chrome(options=chrome_options)
    
    # 隱藏 webdriver 標記
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver


def wait_random():
    """隨機等待，模擬人類行為"""
    time.sleep(random.uniform(1, 3))


def scrape_hkjc_handicap(date: str = None) -> List[dict]:
    """
    從 HKJC 抓取讓球盤數據
    
    Args:
        date: 日期 (YYYY-MM-DD)，預設今日
        
    Returns:
        賽事列表
    """
    if not date:
        date = datetime.now(HKT).strftime("%Y-%m-%d")
    
    driver = None
    matches = []
    
    try:
        print("🚀 啟動瀏覽器...")
        driver = create_driver()
        
        # 訪問 HKJC 足球頁面
        url = "https://bet.hkjc.com/ch/football/home"
        print(f"📡 訪問: {url}")
        driver.get(url)
        
        # 等待頁面加載
        wait_random()
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "match-list"))
        )
        
        print("✅ 頁面加載完成")
        wait_random()
        
        # 獲取頁面源碼
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # 查找所有賽事
        # HKJC 結構可能需要根據實際頁面調整
        match_elements = soup.find_all('div', class_='match-row') or \
                        soup.find_all('tr', class_='match') or \
                        soup.find_all('div', attrs={'data-match-id': True})
        
        print(f"📊 找到 {len(match_elements)} 個賽事元素")
        
        # 如果沒找到，嘗試其他方式
        if not match_elements:
            # 查找包含讓球信息的元素
            all_text = soup.get_text()
            print(f"📝 頁面文本長度: {len(all_text)} chars")
            
            # 嘗試查找特定模式
            import re
            # 匹配 FB code 和 讓球盤 odds
            handicap_pattern = re.findall(
                r'FB(\d+).*?([\d.]+)\s*/\s*([\d.]+)',
                all_text
            )
            print(f"🔍 找到 {len(handicap_pattern)} 個可能既讓球赔率")
        
        # 嘗試點擊"讓球"選項卡
        try:
            handicap_tab = driver.find_element(By.XPATH, "//a[contains(text(), '讓球')]")
            handicap_tab.click()
            wait_random()
            print("✅ 切換到讓球盤")
        except Exception as e:
            print(f"⚠️ 找不到讓球選項: {e}")
        
        # 重新獲取頁面
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        # 解析賽事數據
        # 這個結構需要根據實際頁面調整
        matches = parse_matches(soup, date)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("👋 瀏覽器已關閉")
    
    return matches


def parse_matches(soup: BeautifulSoup, date: str) -> List[dict]:
    """解析賽事數據"""
    matches = []
    
    # 嘗試多种可能的結構
    # 結構1: table rows
    rows = soup.find_all('tr', class_=lambda x: x and 'match' in x.lower())
    
    for row in rows:
        try:
            # 提取 FB code
            code_elem = row.find('td', class_='match-code') or \
                       row.find('span', class_='code')
            if not code_elem:
                continue
            
            code = code_elem.text.strip()
            if not code.startswith('FB'):
                continue
            
            # 提取球隊
            home_elem = row.find('td', class_='home-team') or \
                       row.find('span', class_='home')
            away_elem = row.find('td', class_='away-team') or \
                       row.find('span', class_='away')
            
            if not (home_elem and away_elem):
                continue
            
            home_team = home_elem.text.strip()
            away_team = away_elem.text.strip()
            
            # 提取讓球線和赔率
            # 通常讓球盤格式: 主隊讓球 / 客隊受讓
            handicap_elem = row.find('td', class_='handicap') or \
                          row.find('span', class_='line')
            
            odds_cells = row.find_all('td', class_='odds')
            
            if len(odds_cells) >= 2:
                home_odds = float(odds_cells[0].text.strip())
                away_odds = float(odds_cells[1].text.strip())
                
                # 推斷讓球線 (需要根據實際數據)
                handicap_line = infer_handicap(home_odds, away_odds)
                
                match = {
                    'fb_code': code,
                    'date': date,
                    'home_team': home_team,
                    'away_team': away_team,
                    'handicap_line': handicap_line,
                    'home_odds': home_odds,
                    'away_odds': away_odds,
                    'status': '未開波',  # 需要從頁面提取
                    'value_rating': '高價值' if home_odds > 1.95 or away_odds > 1.95 else '一般'
                }
                matches.append(match)
                
        except Exception as e:
            continue
    
    return matches


def infer_handicap(home_odds: float, away_odds: float) -> float:
    """根據赔率推斷讓球線"""
    # 赔率差異越大，讓球線越大
    diff = abs(home_odds - away_odds)
    
    if diff < 0.1:
        return 0.0
    elif diff < 0.3:
        return 0.25
    elif diff < 0.5:
        return 0.5
    elif diff < 0.8:
        return 0.75
    elif diff < 1.2:
        return 1.0
    elif diff < 1.7:
        return 1.5
    elif diff < 2.2:
        return 2.0
    else:
        return 2.5


if __name__ == "__main__":
    # 測試
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"🧪 測試爬蟲 (date={date})...")
    results = scrape_hkjc_handicap(date)
    print(f"\n📊 結果: {len(results)} 場賽事")
    for m in results[:5]:
        print(f"  {m}")
