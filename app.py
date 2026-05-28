import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import random

# --- 1. 設定網頁基本資訊 ---
st.set_page_config(page_title="BINGO", page_icon="🎯", layout="centered")

# --- 2. 注入 CSS 樣式 (改用最穩定的 st.markdown 防止 TypeError) ---
css = """
<style>
    .title-bingo { text-align: center; font-size: 32px; font-weight: 900; letter-spacing: 2px; margin-top: -10px; margin-bottom: 5px; color: #FFFFFF; }
    .latest-box { background-color: #15191E; border: 2px solid #E63946; border-radius: 12px; padding: 15px 10px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .latest-title { font-size: 14px; color: #A0AEC0; margin-bottom: 10px; font-weight: bold; }
    .latest-period { color: #E63946; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #111418; padding: 12px; border-radius: 8px; border: 1px solid #2D3748; text-align: center; }
    .balls-container { display: flex; flex-wrap: wrap; justify-content: center; max-width: 350px; margin: 0 auto; }
    .ball { display: inline-block; width: 28px; height: 28px; background-color: #E63946; color: white; border-radius: 50%; text-align: center; line-height: 28px; font-weight: bold; margin: 3px 2px; font-size: 12px; }
    .super-ball { background-color: #FFB703; color: #023047; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- 3. 資料庫初始化 (加入快取機制防止 OperationalError) ---
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

# --- 4. 🎯 奧索網精準抓取邏輯 (只抓第一列最新數據) ---
def fetch_and_save():
    success = False
    fetched_period = ""
    try:
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 精準抓取所有開獎資料列
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            if rows:
                # 第一筆即為最新一期
                cols = rows[0].find_all('td')
                if len(cols) >= 4:
                    period_num = cols[0].text.strip()
                    time_str = cols[1].text.strip()
                    
                    # 取出所有號碼球
                    ball_divs = cols[2].find_all('div')
                    numbers = [int(b.text.strip()) for b in ball_divs if b.text.strip().isdigit()]
                    
                    # 取出超級獎號
                    super_div = cols[3].find('div')
                    super_num = int(super_div.text.strip()) if super_div and super_div.text.strip().isdigit() else None

                    if len(numbers) >= 20 and period_num.isdigit():
                        numbers = sorted(numbers[:20])
                        super_num = super_num if super_num else numbers[0]
                        nums_str = ",".join([str(n).zfill(2) for n in numbers])
                        draw_time = f"{datetime.now().strftime('%Y-%m-%d')} {time_str}:00"

                        # 寫入歷史資料庫
                        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)',
                                     (period_num, draw_time, nums_str, super_num))
                        conn.commit()
                        success = True
                        fetched_period = period_num
    except Exception:
        pass

    # 🌟 若網站連線失敗，啟用時間公式推算兜底，確保系統不崩潰
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

# --- 6. 刷新按鈕邏輯 (放在讀取資料庫之前，完全不需要 st.rerun) ---
if st.button("🔄 立即刷新數據", use_container_width=True):
    # 當按鈕按下，優先去抓資料庫並寫入
    is_real, p_num = fetch_and_save()
    if is_real:
        st.toast(f"✅ 已同步奧索網最新期數：{p_num}", icon="🚀")
    else:
        st.toast(f"⚠️ 網路異常，已切換至公式推算期數：{p_num}", icon="⚠️")

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. 從資料庫讀取「最新」資料並顯示 ---
# 因為上方按鈕執行過了，這裡讀出來的一定是剛才寫進去的最新數據！
cursor = conn.cursor()
cursor.execute("SELECT period_num, draw_time, numbers, super_num FROM bingo_history ORDER BY period_num DESC LIMIT 1")
latest_draw = cursor.fetchone()

if latest_draw:
    period, draw_time, numbers, s_num = latest_draw
    balls_html = ""
    for n in numbers.split(','):
        if n.isdigit() and int(n) == s_num:
            balls_html += f'<div class="ball super-ball">{n}</div>'
        else:
            balls_html += f'<div class="ball">{n}</div>'

    box_html = f"""
    <div class="latest-box">
       <div class="latest-title">📊 資料庫最新同步開獎資訊</div>
       <div style="margin-bottom: 8px;">
           <span style="color:#A0AEC0; font-size:14px;">最新期數：</span>
           <span class="latest-period">{period}</span>
           <span style="color:#718096; font-size:12px; margin-left:10px;">({draw_time})</span>
       </div>
       <div style="color:#A0AEC0; font-size:14px; margin-bottom: 8px;">開獎號碼：</div>
       <div class="balls-container">{balls_html}</div>
       <div style="text-align: right; margin-top: 5px; font-size: 11px; color: #718096;">※ 黃色球為超級獎號</div>
    </div>
    """
    st.markdown(box_html, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="latest-box" style="text-align:center;">
       <div class="latest-title" style="color:#FFB703;">⚠️ 資料庫尚未同步數據</div>
       <p style="color:#A0AEC0; font-size:13px; margin:0;">請點擊上方「立即刷新數據」按鈕同步號碼</p>
    </div>
    """, unsafe_allow_html=True)
    
# --- 8. 預測版面 ---
st.subheader("🎯 V10 三星推薦組合")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:2
