import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="BINGO V10", page_icon="🎯", layout="centered")

# --- 2. CSS 樣式配置 (精準 10 欄雙排網格) ---
st.markdown("""
<style>
    .title-bingo { text-align: center; font-size: 32px; font-weight: 900; margin-bottom: 10px; color: #FFFFFF; }
    .latest-box { background-color: #15191E; border: 2px solid #E63946; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .latest-title { font-size: 14px; color: #A0AEC0; margin-bottom: 10px; font-weight: bold; }
    .latest-period { color: #E63946; font-size: 18px; font-weight: bold; }
    .metric-card { background-color: #111418; padding: 12px; border-radius: 8px; border: 1px solid #2D3748; text-align: center; }
    
    /* 10欄網格，手機與網頁完美切成兩排 */
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

# --- 4. 核心數據同步邏輯 (已綁定您專屬的 Google GAS 跳板) ---
def fetch_and_save():
    success = False
    new_periods_count = 0
    tw_now = datetime.utcnow() + timedelta(hours=8)
    
    # 已自動嵌入您佈署的 Google 代理伺服器網址
    GAS_URL = "https://script.google.com/macros/s/AKfycbxyYuX-Okda8nb5Kbr7HS-cw2bqnxOrQl_BUKBc_-CwbFFMyS0dZ7717u5tSN8zG2Xa/exec"

    try:
        # 透過 Google 伺服器去抓取網頁，完美繞過海外 IP 封鎖
        res = requests.get(GAS_URL, timeout=15)
        
        if res.status_code == 200 and not res.text.startswith("Error"):
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle'])
            
            cursor = conn.cursor()
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
                        
                        cursor.execute("SELECT 1 FROM bingo_history WHERE period_num = ?", (p_num,))
                        if not cursor.fetchone():
                            new_periods_count += 1
                            
                        conn.execute('INSERT OR REPLACE INTO bingo_history VALUES (?, ?, ?, ?)', (p_num, d_time, nums_str, s_num))
                        success = True
            conn.commit()
            msg = f"✅ 成功經由 Google 數據中心同步！已寫入官方最新真實開獎數據 (新增 {new_periods_count} 期)。"
        else:
            msg = f"❌ 轉接錯誤：Google 跳板回傳異常，請檢查 Google Apps Script 的部署權限是否設為「任何人」。"
    except Exception as e:
        msg = f"❌ 連線失敗：無法串接 Google 代理伺服器 ({str(e)})"

    st.session_state['refresh_status'] = {'is_ok': success, 'msg': msg, 'triggered': True}

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
    st.info("ℹ️ 資料庫目前尚無真實紀錄。請點擊下方按鈕，透過 Google 代理完成首次精準數據同步。")

# --- 7. 立即刷新數據按鈕 (精確配置在開獎資訊正下方) ---
st
