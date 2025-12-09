import streamlit as st
import pandas as pd
import numpy as np

# 頁面設定
st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide")

# 主標題
st.title("YIP SHING Project Status Dashboard")

# 中間輸入區
st.markdown("### 查詢 Project 狀態")
project_input = st.text_area(
    "請輸入一個或多個 Project 名稱或 ID（每行一個，或用逗號分隔）",
    height=150,
    placeholder="例如:\nProject-001\nYIP-2025-01\nNew Building Project"
)

# 側邊欄（可選）
st.sidebar.header("導航")
st.sidebar.info("輸入 Project 名稱後，每個 Project 會變成可展開的區塊，點擊名稱即可查看詳細資料。")

# 處理輸入的 Project 清單
if project_input.strip():
    # 支援逗號或換行分隔
    raw_projects = project_input.replace(",", "\n").split("\n")
    projects = [p.strip() for p in raw_projects if p.strip()]

    if projects:
        st.success(f"找到 {len(projects)} 個 Project，點擊下方名稱展開查看詳細資料")

        for idx, project_name in enumerate(projects, start=1):
            # 每個 Project 都用 expander 包裝，可點擊展開
            with st.expander(f"📌 {project_name} (點擊展開詳細狀態)", expanded=False):
                st.subheader(f"Project: {project_name}")

                # 四個關鍵指標
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("整體進度", "78%", "+5%")
                with col2:
                    st.metric("任務完成數", "45 / 60", "-2")
                with col3:
                    st.metric("風險等級", "中", "穩定")
                with col4:
                    st.metric("預算使用率", "62%", "+8%")

                # 進度圖表
                st.markdown("**進度趨勢圖**")
                chart_data = pd.DataFrame(
                    {
                        "週數": range(1, 11),
                        "實際進度": np.cumsum(np.random.randint(5, 15, size=10)),
                        "計劃進度": np.cumsum(np.full(10, 10))
                    }
                ).set_index("週數")
                st.line_chart(chart_data)

                # 任務表格
                st.markdown("**任務狀態**")
                task_data = pd.DataFrame({
                    "任務名稱": ["需求分析", "系統設計", "開發階段", "測試驗證", "上線部署"],
                    "負責人": ["張三", "李四", "王五", "趙六", "錢七"],
                    "狀態": ["完成", "完成", "進行中", "進行中", "待開始"],
                    "截止日期": ["2025-10-15", "2025-11-01", "2025-12-20", "2026-01-15", "2026-02-01"]
                })
                st.dataframe(task_data, use_container_width=True, hide_index=True)

                # 備註或額外資訊
                st.info("最後更新時間：2025-12-09 | 資料來源：內部 PM 系統")
    else:
        st.warning("請輸入有效的 Project 名稱。")
else:
    st.info("👈 請在上方文字區域輸入 Project 名稱或 ID（支援多個），輸入後每個 Project 會顯示為可展開的區塊。")
    st.markdown("""
    ### 歡迎使用 YIP SHING Project Status Dashboard

    此 Dashboard 讓您：
    - 快速查詢一個或多個專案狀態
    - 點擊專案名稱展開查看詳細進度、圖表與任務
    - 支援批量輸入，方便同時追蹤多個專案
    """)

# 底部
st.caption("Powered by Streamlit | 更新日期：2025-12-09")