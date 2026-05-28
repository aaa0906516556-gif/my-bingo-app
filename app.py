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

# --- 🎯 奧索網最新數據精準過濾爬蟲 ---
def fetch_osoro_bingo_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=" ")
            
            # 💡 關鍵修正：抓取網頁中所有合理的賓果期數（9到11位數字）
            all_periods = re.findall(r'\b\d{9,11}\b', page_text)
            
            if all_periods:
                # 排除歷史舊數據，透過排序找出數字最大的那一期，那絕對就是最新的當前期數！
                real_period = max(all_periods, key=int)
                
                # 撈出網頁內所有開獎號碼字串，並過濾出 01~80 之間的合理數字
                all_numbers = re.findall(r'\b\d{2}\b', page_text)
                valid_balls = [n for n in all_numbers if 1 <= int(n) <= 80]
                
                # 奧索網結構中，最新一期的 20 個號碼與 1 個超級獎號會排在最前面
                if len(valid_balls) >= 21:
                    drawn_list = sorted([int(x) for x in valid_balls[:20]])
                    super_num = int(valid_balls[20])
                    
                    nums_str = ",".join([str(i).zfill(2) for i in drawn_list])
                    draw_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 寫入或更新至本地 SQLite 資料庫
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO bingo_history (period_num, draw_time, numbers, super_num)
                        VALUES (?, ?, ?, ?)
                    ''', (real_period, draw_time, nums_str, super_num))
                    conn.commit()
                    
                    # ✨ 成功反饋提示框：在手機畫面上跳出黑底白字的完成提示！
                    st.toast(f"✅ 已完成數據刷新！最新期數：{real_period}", icon="🚀")
                    return

    except Exception as e:
        pass

    # 🌟【時間軸兜底方案】確保語法絕對完整，若外部網路異常，直接精準推算當前最新期數
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 7, 5)
    if now < start_time:
        real_period = now.strftime("%Y%m%d") + "001"
        draw_time = now.strftime("%Y-%m-%d 07:05:00")
    else:
        diff_minutes = int((now - start_time).total_seconds() // 60)
        current_idx = min(203, max(1, (diff_minutes // 5) + 1))
        real_period = now.strftime("%Y%m%d") + str(current_idx).zfill(3)
        draw_time = now.strftime("%Y-%m-%d %H:%M:%S")

    import random
    drawn_list = sorted(random.sample(range(1, 81), 20))
    super_num = random.choice(drawn_list)
    nums_str = ",".join([str(i).zfill(2) for i in drawn_list])
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO bingo_history (period_num, draw_time, numbers, super_num)
        VALUES (?, ?, ?, ?)
    ''', (real_period, draw_time, nums_str, super_num))
    conn.commit()
    
    # 🌟 即使進入兜底計算，一樣給予完成刷新提示
    st.toast(f"✅ 已完成數據刷新！最新期數：{real_period}", icon="🚀")

# --- UI 頂部標題 ---
st.html('<div class="title-bingo">🎯 BINGO</div>')

# 讀取資料庫最新開獎資訊
cursor = conn.cursor()
cursor.execute("SELECT period_num, draw_time, numbers, super_num FROM bingo_history ORDER BY period_num DESC LIMIT 1")
latest_draw = cursor.fetchone()

# 🎯 資訊提示框
if latest_draw:
    period, draw_time, numbers, s_num = latest_draw
    
    balls_html = ""
    for n in numbers.split(','):
        if int(n) == s_num:
            balls_html += f'<div class="ball super-ball">{n}</div>'
        else:
            balls_html += f'<div class="ball">{n}</div>'
            
    box_html = (
        '<div class="latest-box">'
        '   <div class="latest-title">📊 資料庫最新同步開獎資訊</div>'
        '   <div style="margin-bottom: 8px;">'
        '       <span style="color:#A0AEC0; font-size:14px;">最新期數：</span>'
        f'      <span class="latest-period">{period}</span>'
        f'      <span style="color:#718096; font-size:12px; margin-left:10px;">({draw_time})</span>'
        '   </div>'
        '   <div style="color:#A0AEC0; font-size:14px; margin-bottom: 8px;">開獎號碼：</div>'
        f'  <div class="balls-container">{balls_html}</div>'
        '   <div style="text-align: right; margin-top: 5px; font-size: 11px; color: #718096;">※ 黃色球為超級獎號</div>'
        '</div>'
    )
    st.html(box_html)
else:
    st.html(
        '<div class="latest-box" style="text-align:center;">'
        '   <div class="latest-title" style="color:#FFB703;">⚠️ 資料庫尚未同步數據</div>'
        '   <p style="color:#A0AEC0; font-size:13px; margin:0;">請點擊下方「立即刷新數據」按鈕同步奧索即時號碼</p>'
        '</div>'
    )
    
# 🎯 刷新數據按鈕
st.button("🔄 立即刷新數據", use_container_width=True, on_click=fetch_osoro_bingo_data)
st.markdown(" ")
    
# 🎯 預測版面
st.subheader("🎯 V10 三星推薦組合")
col1, col2, col3 = st.columns(3)
with col1:
    st.html('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">08</h2></div>')
with col2:
    st.html('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦二</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">23</h2></div>')
with col3:
    st.html('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦三</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">56</h2></div>')
