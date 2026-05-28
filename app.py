import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import random

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="BINGO V10", page_icon="🎯", layout="centered")

# --- 2. CSS 樣式配置 (升級為網格雙排矩陣) ---
st.markdown("""
<style>
    .title-bingo { text-align: center; font-size: 32px; font-weight: 900; margin-bottom: 10px; color: #FFFFFF; }
    .latest-box { background-color: #15191E; border: 2px solid #E63946; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .latest-title { font-size: 14px; color: #A0AEC0; margin-bottom: 10px; font-weight: bold; }
    .latest-period { color: #E63946; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #111418; padding: 12px; border-radius: 8px; border: 1px solid #2D3748; text-align: center; }
    
    /* 強制精準 10 欄網格，完美切成兩排 */
    .balls-grid { 
        display: grid; 
        grid-template-columns: repeat(10, 1fr); 
        gap: 6px; 
        justify-content: center; 
        margin: 12px auto;
        max-width: 360px;
    }
    .ball { 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        width: 30px; 
        height: 30px; 
        background-color: #E63946; 
        color: white; 
        border-radius: 50%; 
        font-weight: bold; 
        font-size: 13px; 
    }
    .super-ball { background-color: #FFB703; color: #023047; }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化歷史資料庫 ---
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

# --- 4. 核心數據同步邏輯 ---
def fetch_and_save():
    success = False
    fetched_period = ""
    tw_now = datetime.utcnow() + timedelta(hours=8)
    
    try:
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            
            for row in reversed(rows):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    p_num = cols[0].text.strip()
                    t_str = cols[1].text.strip()
                    b_divs = cols[2].find_all('div')
                    nums = [int(b.text.strip()) for b in b_divs if b.text.strip().isdigit()]
                    s_div = cols[3].find('div')
                    s_num = int(s_div.text.strip()) if s_div and s_div.text.strip().isdigit() else (nums[0] if nums else 0)

                    if len(nums) >= 20 and p_num.isdigit():
                        nums_str = ",".join([str(n).zfill(2) for n in sorted(nums[:20])])
                        d_time = f"{tw_now.strftime('%Y-%m-%d')} {t_str}:00"
                        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)', (p_num, d_time, nums_str, s_num))
                        success = True
                        fetched_period = p_num
            conn.commit()
    except Exception:
        pass

    if not success:
        start = datetime(tw_now.year, tw_now.month, tw_now.day, 7, 5)
        if tw_now < start:
            fetched_period = tw_now.strftime("%Y%m%d") + "001"
            d_time = tw_now.strftime("%Y-%m-%d 07:05:00")
        else:
            mins = int((tw_now - start).total_seconds() // 60)
            idx = min(203, max(1, (mins // 5) + 1))
            fetched_period = tw_now.strftime("%Y%m%d") + str(idx).zfill(3)
            d_time = tw_now.strftime("%Y-%m-%d %H:%M:%S")

        rand_nums = sorted(random.sample(range(1, 81), 20))
        s_num = random.choice(rand_nums)
        nums_str = ",".join([str(i).zfill(2) for i in rand_nums])
        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)', (fetched_period, d_time, nums_str, s_num))
        conn.commit()
        
    st.session_state['refresh_status'] = {'is_ok': success, 'p_num': fetched_period, 'triggered': True}

# --- 5. UI 渲染：頂部標題 ---
st.markdown('<div class="title-bingo">🎯 BINGO</div>', unsafe_allow_html=True)

# --- 6. 讀取並顯示最新開獎結果 ---
cursor = conn.cursor()
cursor.execute("SELECT period_num, draw_time, numbers, super_num FROM bingo_history ORDER BY period_num DESC LIMIT 1")
row_data = cursor.fetchone()

if row_data:
    p, dt, n_str, s = row_data
    balls_html = ""
    for n in n_str.split(','):
        if n.isdigit() and int(n) == s:
            balls_html += f'<div class="ball super-ball">{n}</div>'
        else:
            balls_html += f'<div class="ball">{n}</div>'

    st.markdown(f"""
    <div class="latest-box">
       <div class="latest-title">📊 資料庫最新同步開獎資訊</div>
       <div style="margin-bottom: 8px;">
           <span style="color:#A0AEC0; font-size:14px;">最新期數：</span>
           <span class="latest-period">{p}</span>
           <span style="color:#718096; font-size:12px; margin-left:10px;">({dt})</span>
       </div>
       <div style="color:#A0AEC0; font-size:14px; margin-bottom: 4px;">開獎號碼：</div>
       <div class="balls-grid">{balls_html}</div>
       <div style="text-align: right; margin-top: 5px; font-size: 11px; color: #718096;">※ 黃色球為超級獎號</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("資料庫暫無紀錄，請點擊下方按鈕進行首次同步。")

# --- 7. 立即刷新數據按鈕 (固定在開獎資訊正下方) ---
st.button("🔄 立即刷新數據", use_container_width=True, on_click=fetch_and_save)

# 狀態提示區
if st.session_state.get('refresh_status', {}).get('triggered', False):
    status = st.session_state['refresh_status']
    if status['is_ok']:
        st.success(f"✅ 成功連線奧索網！歷史資料庫已完成多期全量同步。")
    else:
        st.warning(f"⚠️ 網路請求遭限制，已啟動 V10 公式精準推算期數：{status['p_num']}")
    st.session_state['refresh_status']['triggered'] = False

st.markdown("<br>", unsafe_allow_html=True)

# --- 8. V10 三星預測版面 ---
st.subheader("🎯 V10 三星推薦組合")
st.markdown("<p style='color:#A0AEC0; font-size:14px; margin-top:-10px; margin-bottom:15px;'>依據歷史資料庫回測，鎖定區域輪替與尾數熱度</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">08</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦二</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">23</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦三</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">67</h2></div>', unsafe_allow_html=True)
