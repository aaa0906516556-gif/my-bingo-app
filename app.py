import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random

# 🚀 設定網頁基本資訊（特別針對手機瀏覽器優化）
st.set_page_config(
    page_title="BINGO",
    page_icon="🎯",
    layout="centered"
)

# 使用標準 st.html 集中注入網頁的所有 CSS 樣式，並優化手機版球體兩排排版
st.html("""
<style>
    /* 標題置中且大小適中 */
    .title-bingo {
        text-align: center;
        font-size: 32px;
        font-weight: 900;
        letter-spacing: 2px;
        margin-top: -10px;
        margin-bottom: 5px;
        color: #FFFFFF;
    }
    /* 最新期數與開獎號碼的專用提示框 */
    .latest-box {
        background-color: #15191E;
        border: 2px solid #E63946;
        border-radius: 12px;
        padding: 15px 10px; /* 稍微縮小左右內邊距以利排版 */
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
    /* 號碼球容器：確保置中且寬度剛好能放 10 顆球 */
    .balls-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        max-width: 350px;
        margin: 0 auto;
    }
    /* 精準調校號碼球大小與間距，確保在手機上完美排成兩排 */
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
    /* 超級獎號球樣式 */
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
    
    # 檢查舊的表格格式，如果缺少新欄位就重新建立它
    try:
        cursor.execute("SELECT draw_time FROM bingo_history LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS bingo_history")
        
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

# --- 模擬爬蟲寫入 ---
def simulate_crawl():
    now = datetime.now()
    simulated_period = now.strftime("%Y%m%d") + str(int(now.strftime("%H%M")) // 5)
    
    drawn_list = sorted(random.sample(range(1, 81), 20))
    super_num = random.choice(drawn_list)
    nums_str = ",".join([str(i).zfill(2) for i in sorted(drawn_list)])
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO bingo_history (period_num, draw_time, numbers, super_num)
        VALUES (?, ?, ?, ?)
    ''', (simulated_period, now.strftime('%Y-%m-%d %H:%M:%S'), nums_str, super_num))
    conn.commit()

# --- UI 頂部標題 ---
st.html('<div class="title-bingo">🎯 BINGO</div>')

# 讀取最新一期資訊
cursor = conn.cursor()
try:
    cursor.execute("SELECT period_num, draw_time, numbers, super_num FROM bingo_history ORDER BY period_num DESC LIMIT 1")
    latest_draw = cursor.fetchone()
except sqlite3.OperationalError:
    latest_draw = None

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
        '   <p style="color:#A0AEC0; font-size:13px; margin:0;">請點擊下方「立即刷新數據」按鈕同步最新期數</p>'
        '</div>'
    )
    
# 🎯 刷新數據按鈕
st.button("🔄 立即刷新數據", use_container_width=True, on_click=simulate_crawl)
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
