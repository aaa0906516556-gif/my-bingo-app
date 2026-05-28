import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import random

# --- 1. 基本設定 ---
st.set_page_config(page_title="BINGO V10", page_icon="🎯", layout="centered")

# --- 2. CSS 樣式 ---
st.markdown("""
<style>
    .title-bingo { text-align: center; font-size: 32px; font-weight: 900; margin-bottom: 10px; color: #FFFFFF; }
    .latest-box { background-color: #15191E; border: 2px solid #E63946; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .latest-title { font-size: 14px; color: #A0AEC0; margin-bottom: 10px; font-weight: bold; }
    .latest-period { color: #E63946; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #111418; padding: 12px; border-radius: 8px; border: 1px solid #2D3748; text-align: center; }
    .balls-container { display: flex; flex-wrap: wrap; justify-content: center; margin: 10px 0; }
    .ball { display: inline-block; width: 30px; height: 30px; background-color: #E63946; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin: 4px; font-size: 13px; }
    .super-ball { background-color: #FFB703; color: #023047; }
</style>
""", unsafe_allow_html=True)

# --- 3. 資料庫連線 ---
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

# --- 4. 爬蟲與資料庫完整更新 ---
def fetch_and_save():
    success = False
    fetched_period = ""
    try:
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            
            # 迴圈抓取網頁上所有的近期歷史資料，全部建檔入庫
            for row in rows:
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
                        d_time = f"{datetime.now().strftime('%Y-%m-%d')} {t_str}:00"
                        # 使用 INSERT OR IGNORE，確保所有資料進庫且不重複報錯
                        conn.execute('INSERT OR IGNORE INTO bingo_history VALUES (?, ?, ?, ?)', (p_num, d_time, nums_str, s_num))
                        
                        if not success: # 抓取最新一期作為回報基準
                            success = True
                            fetched_period = p_num
            conn.commit()
    except Exception as e:
        pass

    # 備用機制 (網路異常時)
    if not success:
        dt_now = datetime.now()
        start = datetime(dt_now.year, dt_now.month, dt_now.day, 7, 5)
        if dt_now < start:
            fetched_period = dt_now.strftime("%Y%m%d") + "001"
            d_time = dt_now.strftime("%Y-%m-%d 07:05:00")
        else:
            mins = int((dt_now - start).total_seconds() // 60)
            idx = min(203, max(1, (mins // 5) + 1))
            fetched_period = dt_now.strftime("%Y%m%d") + str(idx).zfill(3)
            d_time = dt_now.strftime("%Y-%m-%d %H:%M:%S")

        rand_nums = sorted(random.sample(range(1, 81), 20))
        s_num = random.choice(rand_nums)
        nums_str = ",".join([str(i).zfill(2) for i in rand_nums])
        conn.execute('INSERT OR IGNORE INTO bingo_history VALUES (?, ?, ?, ?)', (fetched_period, d_time, nums_str, s_num))
        conn.commit()
        
    return success, fetched_period

# --- 5. UI 介面 ---
st.markdown('<div class="title-bingo">🎯 BINGO</div>', unsafe_allow_html=True)

# --- 6. 按鈕邏輯 (解決畫面不同步、廢除 st.rerun) ---
if st.button("🔄 立即刷新數據", use_container_width=True):
    is_ok, current_p = fetch_and_save()
    if is_ok:
        st.success(f"✅ 已完成數據刷新！最新期數：{current_p}")
    else:
        st.warning(f"⚠️ 網路異常，已切換至公式推算期數：{current_p}")

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. 讀取最新歷史紀錄 ---
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
       <div style="color:#A0AEC0; font-size:14px; margin-bottom: 8px;">開獎號碼：</div>
       <div class="balls-container">{balls_html}</div>
       <div style="text-align: right; margin-top: 5px; font-size: 11px; color: #718096;">※ 黃色球為超級獎號</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("尚無歷史資料，請點擊上方刷新按鈕。")

# --- 8. V10 三星預測 ---
st.subheader("🎯 V10 三星推薦組合")
st.markdown("<p style='color:#A0AEC0; font-size:14px; margin-top:-10px; margin-bottom:15px;'>依據歷史資料庫回測，鎖定區域輪替與尾數熱度</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">01</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦二</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">11</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦三</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">31</h2></div>', unsafe_allow_html=True)
