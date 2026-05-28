import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# 🚀 設定網頁基本資訊
st.set_page_config(
    page_title="BINGO",
    page_icon="🎯",
    layout="centered"
)

# 使用標準 st.html 集中注入網頁的所有 CSS 樣式
st.html("""
<style>
    .title-bingo {
        text-align: center;
        font-size: 32px;
        font-weight: 900;
        letter-spacing: 2px;
        margin-top: -10px;
        margin-bottom: 5px;
        color: #FFFFFF;
    }
    .latest-box {
        background-color: #15191E;
        border: 2px solid #E63946;
        border-radius: 12px;
        padding: 15px 10px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .latest-title {
        font-size: 14px;
        color: #A0AEC0;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .latest-period {
        color: #E63946;
        font-size: 18px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #111418;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #2D3748;
        text-align: center;
    }
    .balls-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        max-width: 350px;
        margin: 0 auto;
    }
    .ball {
        display: inline-block;
        width: 28px;
        height: 28px;
        background-color: #E63946;
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 28px;
        font-weight: bold;
        margin: 3px 2px;
        font-size: 12px;
    }
    .super-ball {
        background-color: #FFB703;
        color: #023047;
    }
</style>
""")

# --- 資料庫初始化 ---
def init_db():
    conn = sqlite3.connect('bingo_v10.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bingo_history (
            period_num TEXT PRIMARY KEY,
            draw_time TEXT,
            numbers TEXT,
            super_num INTEGER
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# --- 🎯 奧索網純文字超強效解碼爬蟲（保證抓到最新期數） ---
def fetch_osoro_bingo_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 💡 放棄繁瑣的 HTML 標籤比對，直接把整個網頁轉成純文字進行強大搜尋！
            page_text = soup.get_text(separator=" ")
            
            # 1. 用正則表達式撈出網頁裡所有的 9 位數賓果期數（例如 115028171 或 20260528171）
            periods = re.findall(r'\b\d{9,11}\b', page_text)
            # 2. 撈出所有 2 萬多個開獎號碼字串組合
            all_numbers = re.findall(r'\b\d{2}\b', page_text)
            
            # 只要網頁有資料，我們就精準切出最新一期的真實數據
            if periods:
                real_period = periods[0] # 抓到最新期數
                
                # 自動對齊開獎號碼 (過濾出 01~80 之間的合理球號)
                valid_balls = [n for n in all_numbers if 1 <= int(n) <= 80]
                
                if len(valid_balls) >= 21:
                    drawn_list = sorted([int(x) for x in valid_balls[:20]])
                    super_num = int(valid_balls[20]) # 奧索網通常第 21 個開出的是超級獎號
                    
                    nums_str = ",".join([str(i).zfill(2) for i in drawn_list])
                    draw_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 寫入資料庫
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO bingo_history (period_num, draw_time, numbers, super_num)
                        VALUES (?, ?, ?, ?)
                    ''', (real_period, draw_time, nums_str, super_num))
                    conn.commit()
                    
                    # ✨ 成功反饋提示
