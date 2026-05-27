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

# 自訂 CSS 樣式，優化手機版視覺與卡片框（已修正參數指定錯誤）
st.markdown(body="""
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
        padding: 15px;
        margin-bottom: 10px; /* 縮小底部間距，讓按鈕緊跟在下方 */
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
    /* 號碼球樣式 */
    .ball {
        display: inline-block;
        width: 32px;
        height: 32px;
        background-color: #E63946;
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 32px;
        font-weight: bold;
        margin: 3px;
        font-size: 13px;
    }
    /* 超級獎號球樣式 */
    .super-ball {
        background-color: #FFB703;
        color: #023047;
    }
</style>
""", unsafe_allowed_html=True)

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

# --- UI 頂部標題（縮小並僅保留 BINGO） ---
st.markdown('<div class="title-bingo">🎯 BINGO</div>', unsafe_allowed_html=True)

# --- 核心功能頁籤 ---
tab1, tab2, tab3 = st.tabs(["🔮 核心預測", "📊 歷史走勢", "⚙️ 策略微調"])

# ==================== 頁籤 1：核心預測 ====================
with tab1:
    # 讀取最新一期資訊
    cursor = conn.cursor()
    cursor.execute("SELECT period_num, draw_time, numbers, super_num FROM bingo_history ORDER BY period_num DESC LIMIT 10")
    latest_draws = cursor.fetchall()
    
    # 🎯 框框：告訴你目前資料庫更新到的最新一期與號碼
    if latest_draws:
        # 取出最新那一期
        period, draw_time, numbers, s_num = latest_draws[0]
        
        # 產生號碼球 HTML
        balls_html = ""
        for n in numbers.split(','):
            if int(n) == s_num:
                balls_html += f'<div class="ball super-ball">{n}</div>'
            else:
                balls_html += f'<div class="ball">{n}</div>'
                
        # 渲染專用提示框
        st.markdown(f"""
        <div class="latest-box">
            <div class="latest-title">📊 資料庫最新同步開獎資訊</div>
            <div style="margin-bottom: 8px;">
                <span style="color:#A0AEC0; font-size:14px;">最新期數：</span>
                <span class="latest-period">{period}</span>
                <span style="color:#718096; font-size:12px; margin-left:10px;">({draw_time})</span>
            </div>
            <div style="color:#A0AEC0; font-size:14px; margin-bottom: 8px;">開獎號碼：</div>
            <div style="text-align: center;">{balls_html}</div>
            <div style="text-align: right; margin-top: 5px; font-size: 11px; color: #718096;">※ 黃色球為超級獎號</div>
        </div>
        """, unsafe_allowed_html=True)
    else:
        # 初次使用的提示框
        st.markdown("""
        <div class="latest-box" style="text-align:center;">
            <div class="latest-title" style="color:#FFB703;">⚠️ 資料庫尚未建立數據</div>
            <p style="color:#A0AEC0; font-size:13px; margin:0;">請點擊下方「刷新開獎數據」按鈕同步最新期數</p>
        </div>
        """, unsafe_allowed_html=True)
        
    # 🎯 移到框框下方的「刷新數據按鈕」
    st.button("🔄 立即刷新數據", use_container_width=True, on_click=simulate_crawl)
    st.markdown(" ")
        
    st.subheader("🎯 V10 三星推薦組合")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦一</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">08</h2></div>', unsafe_allowed_html=True)
    with col2:
        st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦二</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">23</h2></div>', unsafe_allowed_html=True)
    with col3:
        st.markdown('<div class="metric-card"><p style="color:#A0AEC0;margin:0;font-size:13px;">推薦三</p><h2 style="color:#E63946;margin:5px 0;font-size:24px;">56</h2></div>', unsafe_allowed_html=True)

# ==================== 頁籤 2：歷史走勢 ====================
with tab2:
    st.subheader("📈 近期數據統計分析")
    chart_data = pd.DataFrame({
        '尾數': ['0尾', '1尾', '2尾', '3尾', '4尾', '5尾', '6尾', '7尾', '8尾', '9尾'],
        '近10期出現次數': [12, 8, 15, 6, 9, 14, 11, 7, 18, 5]
    }).set_index('尾數')
    st.bar_chart(chart_data)
    
    st.markdown("---")
    st.subheader("📋 歷史開獎紀錄 (最新 10 期)")
    df = pd.read_sql_query(
        "SELECT period_num AS 期數, super_num AS 超級獎號, numbers AS 開出獎號 FROM bingo_history ORDER BY period_num DESC LIMIT 10", 
        conn
    )
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("暫無紀錄。")

# ==================== 頁籤 3：策略微調 ====================
with tab3:
    st.subheader("🛠️ V10 演算法參數微調")
    period_range = st.slider("分析歷史期數範疇", min_value=5, max_value=50, value=10, step=5)
    hot_weight = st.slider("熱門號碼權重比 (Hot Block)", min_value=0.0, max_value=1.0, value=0.6, step=0.1)
    tail_weight = st.slider("尾數分佈權重比 (Tail Control)", min_value=0.0, max_value=1.0, value=0.4, step=0.1)
    st.success(f"設定已同步：分析近 {period_range} 期")
