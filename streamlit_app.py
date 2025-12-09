import streamlit as st
import pandas as pd
import numpy as np

# 設定頁面標題和佈局（寬版）
st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide")

# 主標題
st.title("YIP SHING Project Status Dashboard")

# 中間輸入 Project
st.markdown("### 查詢 Project 狀態")
project_input = st.text_input("請輸入 Project 名稱或 ID", placeholder="例如: Project-001 或 YIP-2025-01")

# 側邊欄：添加一些導航或額外選項
st.sidebar.header("導航與設定")
view_mode = st.sidebar.selectbox("選擇視圖模式", ["Project 詳細狀態", "所有 Project 概覽", "報告匯出"])
st.sidebar.info("此 Dashboard 用於追蹤 YIP SHING 專案進度。")

# 如果有輸入 Project，顯示詳細狀態
if project_input:
    st.success(f"正在顯示 Project: **{project_input}** 的狀態")

    # 模擬一些數據（實際應用可連接資料庫或 CSV）
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="整體進度", value="78%", delta="+5% (本週)")
    with col2:
        st.metric(label="任務完成數", value="45 / 60", delta="-2")
    with col3:
        st.metric(label="風險等級", value="中", delta="穩定")
    with col4:
        st.metric(label="預算使用率", value="62%", delta="+8%")

    st.markdown("#### 進度圖表")
    # 模擬進度資料
    chart_data = pd.DataFrame(
        np.random.randn(10, 2),
        columns=["實際進度", "計劃進度"]
    )
    chart_data["週數"] = range(1, 11)
    st.line_chart(chart_data.set_index("週數"))

    st.markdown("#### 任務狀態表格")
    task_data = pd.DataFrame({
        "任務名稱": ["需求分析", "設計階段", "開發中", "測試", "部署"],
        "負責人": ["張三", "李四", "王五", "趙六", "錢七"],
        "狀態": ["完成", "完成", "進行中", "待開始", "待開始"],
        "截止日期": ["2025-10-01", "2025-11-01", "2025-12-15", "2026-01-10", "2026-02-01"]
    })
    st.dataframe(task_data, use_container_width=True)

else:
    st.info("👈 請在上方輸入 Project 名稱或 ID 以查看詳細狀態。")
    st.markdown("#### 歡迎使用 YIP SHING Project Status Dashboard")
    st.markdown("此工具可幫助您快速查詢專案進度、風險與任務狀態。")

# 底部說明
st.caption("Powered by Streamlit | 資料來源：內部系統（模擬）")