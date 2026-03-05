"""
HKJC Selenium Scraper - 簡化版
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


def scrape_hkjc():
    """抓取 HKJC 數據"""
    driver = None
    
    try:
        print("🚀 啟動瀏覽器...")
        driver = create_driver()
        
        url = "https://bet.hkjc.com/ch/football/home"
        print(f"📡 訪問: {url}")
        driver.get(url)
        
        # 等待頁面加載
        time.sleep(5)
        
        # 獲取頁面
        html = driver.page_source
        print(f"📄 獲取 HTML: {len(html)} chars")
        
        # 保存 HTML 以便調試
        with open('/tmp/hkjc.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 已保存 HTML 到 /tmp/hkjc.html")
        
        soup = BeautifulSoup(html, 'lxml')
        
        # 嘗試找賽事表格
        # HKJC 使用 table 結構
        tables = soup.find_all('table')
        print(f"📊 找到 {len(tables)} 個表格")
        
        # 找包含 "FB" 的行
        import re
        text = soup.get_text()
        
        # 找 FB codes
        fb_codes = re.findall(r'FB(\d{4})', text)
        print(f"🔢 找到 FB codes: {fb_codes[:10]}")
        
        # 找赔率
        odds_matches = re.findall(r'(\d+\.\d+)', text)
        print(f"💰 找到 {len(odds_matches)} 個赔率")
        
        return {
            'fb_codes': fb_codes,
            'sample_odds': odds_matches[:20]
        }
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("👋 瀏覽器已關閉")
    
    return {}


if __name__ == "__main__":
    result = scrape_hkjc()
    print("\n📊 結果:")
    print(result)
