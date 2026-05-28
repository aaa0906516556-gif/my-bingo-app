import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import random

# --- 1. 設定網頁基本資訊 ---
st.set_page_config(page_title="BINGO", page_icon="🎯", layout="centered")

# --- 2. 注入 CSS 樣式 (獨立字串，100% 安全) ---
css = """
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
"""
st.markdown(css, unsafe_allow_html=True)

# --- 3. 資料庫初始化 ---
@st.cache_resource
def init_db():
    conn = sqlite3.connect('bingo_v10.db', check_same_thread=False)
    conn.execute('''
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

# --- 4. 奧索網網頁爬蟲精準抓取邏輯 ---
def fetch_and_save():
    success = False
    fetched_period = ""
    try:
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            if rows:
                cols = rows[0].find_all('td')
                if len(cols) >= 4:
                    period_num = cols[0].text.strip()
                    time_str = cols[1].text.strip()
                    
                    ball_divs = cols[2].find_all('div')
                    numbers = [int(b.text.strip()) for b in ball_divs if b.text.strip().isdigit()]
                    
                    super_div = cols[3].find('div')
                    super_num = int(super_div.text.strip()) if super_div and super_div.text.strip().isdigit() else None

                    if len(numbers) >= 20 and period_num.isdigit():
                        numbers = sorted(numbers[:20])
                        super_num = super_num if super_num else numbers[0]
                        nums_str = ",".join([str(n).zfill(2) for n in numbers])
                        draw_time = f"{datetime.now().strftime('%Y-%m-%d')} {time_str}:00"

                        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)',
                                     (period_num, draw_time, nums_str, super_num))
                        conn.commit()
                        success = True
                        fetched_period = period_num
    except Exception:
        pass

    if not success:
        now = datetime.now()
        start_time = datetime(now.year, now.month, now.day, 7, 5)
        if now < start_time:
            fetched_period = now.strftime("%Y%m%d") + "001"
            draw_time = now.strftime("%Y-%m-%d 07:05:00")
        else:
            diff_minutes = int((now - start_time).total_seconds() // 60)
            current_idx = min(203, max(1, (diff_minutes // 5) + 1))
            fetched_period = now.strftime("%Y%m%d") + str(current_idx).zfill(3)
            draw_time = now.strftime("%Y-%m-%d %H:%M:%S")

        drawn_list = sorted(random.sample(range(1, 81), 20))
        super_num = random.choice(drawn_list)
        nums_str = ",".join([str(i).zfill(2) for i in drawn_list])

        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)',
                     (fetched_period, draw_time, nums_str, super_num))
        conn.commit()
        
    return success, fetched_period

# --- 5. UI 頂部標題 ---
st.markdown('<div class="title-bingo">🎯 BINGO</div>', unsafe_allow_html=True)

# --- 6. 刷新按鈕邏輯 (按鈕點擊後，程式重跑，優先執行資料庫寫入) ---
if st.button("🔄 立即刷新數據", use_container_width=True):
    is_real, p_num = fetch
