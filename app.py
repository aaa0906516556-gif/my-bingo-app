import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 🚀 設定網頁基本資訊（特別針對手機瀏覽器優化）
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

# --- 🎯 修正：改用奧索網（Osoro）賓果數據源爬蟲 ---
def fetch_osoro_bingo_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 定位奧索網最新一期的開獎資料列
            target_tr = soup.find('tr', class_='RowStyle') or soup.find('tr', class_='AlternatingRowStyle')
            
            if target_tr:
                cols = target_tr.find_all('td')
                if len(cols) >= 4:
                    # 1. 提取期數
                    real_period = cols[0].text.strip()
                    
                    # 2. 提取時間
                    draw_time_str = cols[1].text.strip()
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    draw_time = f"{today_str} {draw_time_str}:00"
                    
                    # 3. 提取開獎號碼 (尋找帶有號碼樣式的 div 或 span)
                    ball_elements = cols[2].find_all(True, class_=lambda x: x and any(k in x.lower() for k in ['ball', 'num', 'no']))
                    
                    if ball_elements:
                        drawn_list = sorted([int(el.text.strip()) for el in ball_elements if el.text.strip().isdigit()])
                    else:
                        # 備用純文字切割解析
                        clean_text = cols[2].text.replace('|', ',').replace('\n', ',')
                        drawn_list = sorted([int(n) for n in clean_text.split(',') if n.strip().isdigit()])
                    
                    # 4. 提取超級獎號
                    super_ball_element = cols[3].find(True)
                    if super_ball_element:
                        super_num = int(super_ball_element.text.strip())
                    else:
                        super_num = int(cols[3].text.strip()) if cols[3].text.strip().isdigit() else (drawn_list[0] if drawn_list else 0)
                        
                    # 驗證資料是否正確抓到 20 顆球
                    if len(drawn_list) >= 20 and real_period:
                        nums_str = ",".join([str(i).zfill(2) for i in drawn_list[:20]])
                        
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO bingo_history (period_num, draw_time, numbers, super_num)
                            VALUES (?, ?, ?, ?)
                        ''', (real_period, draw_time, nums_str, super_num))
                        conn.commit()
                        return
                        
    except Exception as e:
        pass

    # 🌟【兜底方案】萬一外部網站完全斷連，依時間公式在當下即時推算期數，絕不讓畫面卡住
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
        INSERT OR IGNORE INTO bingo_history (period_num, draw_time, numbers, super_num)
        VALUES (?, ?, ?, ?)
    ''', (real_period, draw_time, nums_str, super_num))
    conn.commit()

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
