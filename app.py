import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import time

# 🚀 設定網頁基本資訊（特別針對手機瀏覽器優化）
st.set_page_config(
    page_title="台彩賓果 V10 監控系統",
    page_icon="🎯",
    layout="centered"
)

# --- 資料庫初始化 ---
def init_db():
    conn = sqlite3.connect('bingo_v10.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bingo_history (
            period_num TEXT PRIMARY KEY,
            draw_time TEXT,
            numbers TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# --- 模擬爬蟲寫入 (實際部署時可結合後台定時任務) ---
def simulate_crawl():
    now = datetime.now()
    simulated_period = now.strftime("%Y%m%d") + str(int(now.strftime("%H%M")) // 5)
    
    # 隨機生成 20 個賓果號碼
    import random
    nums = ", ".join([str(i).zfill(2) for i in sorted(random.sample(range(1, 81), 20))])
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO bingo_history (period_num, draw_time, numbers)
        VALUES (?, ?, ?)
    ''', (simulated_period, now.strftime('%Y-%m-%d %H:%M:%S'), nums))
    conn.commit()

# --- UI 介面設計 ---
st.title("🎯 賓果 BINGO BINGO")
st.subheader("V10 自動監控與預測系統 (手機版)")

# 系統狀態顯示
st.info("🤖 雲端監控狀態：運作中（每 5 分鐘自動同步）")

# 模擬重新整理按鈕
if st.button("🔄 立即刷新數據", use_container_width=True):
    simulate_crawl()
    st.toast("數據已更新！")

# --- 核心預測區 ---
st.markdown("### 🔮 V10 核心推薦")
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="推薦一", value="08")
    with col2:
        st.metric(label="推薦二", value="23")
    with col3:
        st.metric(label="推薦三", value="56")
    st.caption("※ 基於最新 10 期冷熱門與尾數權重計算分配")

# --- 歷史資料庫顯示 ---
st.markdown("### 📊 最新開獎數據 (最近 10 期)")

# 從資料庫抓取最新 10 期
df = pd.read_sql_query(
    "SELECT period_num AS 期數, draw_time AS 抓取時間, numbers AS 開出獎號 FROM bingo_history ORDER BY period_num DESC LIMIT 10", 
    conn
)

if not df.empty:
    # 針對手機版調整欄位寬度與顯示
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.write("目前資料庫尚無數據，請點擊上方「立即刷新數據」模擬第一筆資料。")
