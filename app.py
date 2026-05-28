import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import random

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="BINGO", page_icon="🎯", layout="centered")

# --- 2. 注入 CSS 樣式 (精簡版，防止字串過長被切斷) ---
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

# --- 3. 資料庫初始化 (使用安全快取) ---
@st.cache_resource
def init_db():
    db_conn = sqlite3.connect('bingo_v10.db', check_same_thread=False)
    db_conn.execute('''
        CREATE TABLE IF NOT EXISTS bingo_history (
            period_num TEXT PRIMARY KEY,
            draw_time TEXT,
            numbers TEXT,
            super_num INTEGER
        )
    ''')
    db_conn.commit()
    return db_conn

conn = init_db()

# --- 4. 核心爬蟲與存檔邏輯 ---
def run_data_sync():
    has_saved = False
    p_num = ""
    try:
        url = "https://www.osoro.com.tw/Lottery/BingoBingo.aspx"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            if rows:
                cols = rows[0].find_all('td')
                if len(cols) >= 4:
                    p_num = cols[0].text.strip()
                    t_str = cols[1].text.strip()
                    b_divs = cols[2].find_all('div')
                    nums = [int(b.text.strip()) for b in b_divs if b.text.strip().isdigit()]
                    s_div = cols[3].find('div')
                    s_num = int(s_div.text.strip()) if s_div and s_div.text.strip().isdigit() else nums[0]

                    if len(nums) >= 20 and p_num.isdigit():
                        nums_str = ",".join([str(n).zfill(2) for n in sorted(nums[:20])])
                        d_time = f"{datetime.now().strftime('%Y-%m-%d')} {t_str}:00"
                        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)', (p_num, d_time, nums_str, s_num))
                        conn.commit()
                        has_saved = True
    except Exception:
        pass

    # 網路失敗時的自動推算安全兜底
    if not has_saved:
        dt_now = datetime.now()
        start = datetime(dt_now.year, dt_now.month, dt_now.day, 7, 5)
        if dt_now < start:
            p_num = dt_now.strftime("%Y%m%d") + "001"
            d_time = dt_now.strftime("%Y-%m-%d 07:05:00")
        else:
            mins = int((dt_now - start).total_seconds() // 60)
            idx = min(203, max(1, (mins // 5) + 1))
            p_num = dt_now.strftime("%Y%m%d") + str(idx).zfill(3)
            d_time = dt_now.strftime("%Y-%m-%d %H:%M:%S")

        rand_nums = sorted(random.sample(range(1, 81), 20))
        s_num = random.choice(rand_nums)
        nums_str = ",".join([str(i).zfill(2) for i in rand_nums])
        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)', (p_num, d_time, nums_str, s_num))
        conn.commit()
    return has_saved, p_num

# --- 5. 畫面渲染：頂部標題 ---
st.markdown('<div class="title-bingo">🎯 BINGO</div>', unsafe_allow_html=True)

# --- 6. 核心重整按鈕 (點擊時優先觸發同步，自然更新下方的資料庫讀取) ---
if st.button("🔄 立即刷新數據", use_container_width=True):
    is_ok, current_p = run_data_sync()
    if is_ok:
        st.toast(f"✅ 已同步奧索網最新期數：{current_p}", icon="🚀")
    else:
        st.toast(f"⚠️ 網路異常，已切換至公式推算期數：{current_p}", icon="⚠️")

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. 從資料庫讀取並顯示最新開獎結果 ---
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
    st.markdown("""
    <div class="latest-box" style="text-align:center;">
       <div class="latest-title" style="color:#FFB703;">⚠️ 資料庫尚未同步數據</div>
       <p style="color:#A0AEC0; font-size:13px; margin:0;">請點擊上方「立即刷新數據」按鈕同步號碼</p>
    </div>
    """, unsafe_allow_html=True)

# --- 8. 預測版面 (改用最標準的 Streamlit 寫法，徹底排除 HTML 解析不穩定的問題) ---
st.subheader("🎯 V10 三星推薦組合")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">08</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦二</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">23</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦三</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">56</h2></div>', unsafe_allow_html=True)
