"""
HKJC Selenium Scraper - 讓球盤版本
"""
import time
import random
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HKT = pytz.timezone('Asia/Hong_Kong')


def create_driver():
    """建立 Chrome headless 瀏覽器"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_handicap():
    """抓取 HKJC 讓球盤數據"""
    driver = None
    
    try:
        print("🚀 啟動瀏覽器...")
        driver = create_driver()
        
        url = "https://bet.hkjc.com/ch/football/home"
        print(f"📡 訪問: {url}")
        driver.get(url)
        
        # 等待頁面加載
        time.sleep(5)
        
        # 點擊 "讓球" tab
        # 先搵讓球既 element
        try:
            # 搵 "讓球" link/button
            handicap_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//li[@id='hdc']"))
            )
            handicap_link.click()
            print("✅ 點擊了讓球tab")
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ 搵唔到讓球tab: {e}")
            # 試其他方式
            try:
                # 搵包含"讓球"既元素
                links = driver.find_elements(By.XPATH, "//span[contains(text(), '讓球')]")
                if links:
                    links[0].click()
                    print("✅ 點擊了讓球 (方法2)")
                    time.sleep(3)
            except:
                pass
        
        # 獲取頁面
        html = driver.page_source
        print(f"📄 獲取 HTML: {len(html)} chars")
        
        # 保存
        with open('/tmp/hkjc_handicap.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 已保存到 /tmp/hkjc_handicap.html")
        
        soup = BeautifulSoup(html, 'lxml')
        
        # 搵賽事 - 用 data-testid 屬性
        # 例如: FB4936_homeTeam, FB4936_HDC_0_1_xxx_odds
        import re
        
        # 搵所有 match-row
        match_rows = soup.find_all('div', class_='match-row')
        print(f"📊 搵到 {len(match_rows)} 個賽事列")
        
        matches = []
        
        for row in match_rows:
            try:
                # 搵 FB code
                fb_id_elem = row.find('div', class_='fb-id')
                if not fb_id_elem:
                    continue
                
                fb_code = fb_id_elem.get_text(strip=True)
                if not fb_code.startswith('FB'):
                    continue
                
                # 搵球隊
                home_team = row.find('div', attrs={'data-testid': f'{fb_code}_homeTeam'})
                away_team = row.find('div', attrs={'data-testid': f'{fb_code}_awayTeam'})
                
                if not (home_team and away_team):
                    continue
                
                home_team = home_team.get_text(strip=True)
                away_team = away_team.get_text(strip=True)
                
                # 搵時間
                time_elem = row.find('div', attrs={'data-testid': f'{fb_code}_matchTime'})
                match_time = time_elem.get_text(strip=True) if time_elem else ''
                
                # 搵讓球線同赔率
                # 讓球 data-testid 格式: FBxxxx_HDC_0_1_xxxxx_odds
                # 讓球線通常係另一個 column
                
                # 搵 odds elements - 所有 data-testid 包含 _odds 既元素
                odds_elems = row.find_all('span', attrs={'data-testid': re.compile(r'_odds$')})
                
                # 通常讓球盤有兩個赔率 (主讓 / 客受)
                # 格式可能係 multiple odds
                
                handicap_odds = []
                for odds_elem in odds_elems:
                    odds_text = odds_elem.get_text(strip=True)
                    try:
                        odds_val = float(odds_text)
                        if odds_val > 1:  # 只取有意義既赔率
                            handicap_odds.append(odds_val)
                    except:
                        pass
                
                # 如果冇咁多odds，嘗試其他方法
                if len(handicap_odds) < 2:
                    # 搵所有 td/div 既 odds class
                    all_odds = row.find_all(class_=re.compile(r'odds'))
                    for o in all_odds:
                        txt = o.get_text(strip=True)
                        try:
                            val = float(txt)
                            if val > 1 and val not in handicap_odds:
                                handicap_odds.append(val)
                        except:
                            pass
                
                # 推斷讓球線
                handicap_line = 0
                if len(handicap_odds) >= 2:
                    diff = abs(handicap_odds[0] - handicap_odds[1])
                    if diff < 0.15:
                        handicap_line = 0
                    elif diff < 0.4:
                        handicap_line = 0.25
                    elif diff < 0.6:
                        handicap_line = 0.5
                    elif diff < 0.9:
                        handicap_line = 0.75
                    elif diff < 1.3:
                        handicap_line = 1.0
                    elif diff < 1.8:
                        handicap_line = 1.5
                    else:
                        handicap_line = 2.0
                
                if len(handicap_odds) >= 2:
                    match = {
                        'fb_code': fb_code,
                        'hkt_time': match_time,
                        'home_team': home_team,
                        'away_team': away_team,
                        'handicap_line': handicap_line,
                        'home_odds': handicap_odds[0],
                        'away_odds': handicap_odds[1] if len(handicap_odds) > 1 else handicap_odds[0],
                        'status': '未開波',
                        'value_rating': '高價值' if max(handicap_odds[0], handicap_odds[1]) > 1.95 else '一般'
                    }
                    matches.append(match)
                    print(f"  ✓ {fb_code}: {home_team} vs {away_team} | 讓{handicap_line} | {handicap_odds[0]}/{handicap_odds[1]}")
                
            except Exception as e:
                continue
        
        print(f"\n📊 總共搵到 {len(matches)} 場讓球盤賽事")
        return matches
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("👋 瀏覽器已關閉")
    
    return []


if __name__ == "__main__":
    result = scrape_handicap()
    print("\n=== 結果 ===")
    for m in result[:10]:
        print(m)
