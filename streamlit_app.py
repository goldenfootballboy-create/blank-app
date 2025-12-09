import streamlit as st
import pandas as pd
from datetime import datetime, date

# 頁面設定
st.set_page_config(page_title="YIP SHING Project Database", layout="wide")
st.title("🗂️ YIP SHING Project Database")

# 初始化資料（關鍵：日期欄位使用 date 類型）
if 'projects' not in st.session_state:
    st.session_state.projects = pd.DataFrame([
        {"ID": "YIP-001", "Project Name": "新大樓建造", "負責人": "張三",
         "開始日期": date(2025, 1, 15), "結束日期": date(2026, 6, 30),
         "狀態": "進行中", "進度 (%)": 45, "預算 (萬)": 8500},
        {"ID": "YIP-002", "Project Name": "系統升級專案", "負責人": "李四",
         "開始日期": date(2025, 3, 1), "結束日期": date(2025, 12, 31),
         "狀態": "規劃中", "進度 (%)": 10, "預算 (萬)": 3200},
        {"ID": "YIP-003", "Project Name": "廠房擴建", "負責人": "王五",
         "開始日期": date(2025, 2, 20), "結束日期": date(2026, 3, 15),
         "狀態": "進行中", "進度 (%)": 68, "預算 (萬)": 12000},
    ])

df = st.session_state.projects.copy()

# 確保日期欄位是 date 類型（重要！）
df["開始日期"] = pd.to_datetime(df["開始日期"]).dt.date
df["結束日期"] = pd.to_datetime(df["結束日期"]).dt.date

# === 側邊欄：新增 Project ===
st.sidebar.header("📝 新增 Project")
with st.sidebar.form("add_project_form"):
    st.write("填寫以下資訊新增專案")
    new_id = st.text_input("Project ID", placeholder="例如: YIP-004")
    new_name = st.text_input("Project Name", placeholder="專案名稱")
    new_manager = st.text_input("負責人")
    new_start = st.date_input("開始日期", value=datetime.today())
    new_end = st.date_input("結束日期", value=datetime.today())
    new_status = st.selectbox("狀態", ["規劃中", "進行中", "延遲", "完成", "暫停"])
    new_progress = st.slider("進度 (%)", 0, 100, 0)
    new_budget = st.number_input("預算 (萬)", min_value=0, step=100)

    submitted = st.form_submit_button("新增 Project")
    if submitted:
        if new_id and new_name and new_manager:
            if new_id in df["ID"].values:
                st.error("Project ID 已存在，請使用不同 ID")
            else:
                new_row = pd.DataFrame([{
                    "ID": new_id,
                    "Project Name": new_name,
                    "負責人": new_manager,
                    "開始日期": new_start.date() if isinstance(new_start, datetime) else new_start,
                    "結束日期": new_end.date() if isinstance(new_end, datetime) else new_end,
                    "狀態": new_status,
                    "進度 (%)": new_progress,
                    "預算 (萬)": new_budget
                }])
                st.session_state.projects = pd.concat([st.session_state.projects, new_row], ignore_index=True)
                st.success(f"已成功新增 Project: {new_id} - {new_name}")
                st.rerun()
        else:
            st.error("請填寫必填欄位：ID、名稱、負責人")

# === 主畫面：可編輯表格 ===
st.markdown("### 📋 所有 Project 清單")

edited_df = st.data_editor(
    df,
    column_config={
        "ID": st.column_config.TextColumn("Project ID", disabled=True),
        "Project Name": st.column_config.TextColumn("專案名稱", required=True),
        "負責人": st.column_config.TextColumn("負責人"),
        "開始日期": st.column_config.DateColumn("開始日期", format="YYYY-MM-DD"),
        "結束日期": st.column_config.DateColumn("結束日期", format="YYYY-MM-DD"),
        "狀態": st.column_config.SelectboxColumn(
            "狀態",
            options=["規劃中", "進行中", "延遲", "完成", "暫停"],
            required=True
        ),
        "進度 (%)": st.column_config.ProgressColumn(
            "進度",
            min_value=0,
            max_value=100,
            format="%d%%"
        ),
        "預算 (萬)": st.column_config.NumberColumn("預算 (萬)", min_value=0, step=100, format="%d"),
    },
    num_rows="dynamic",  # 允許直接增刪列
    use_container_width=True,
    hide_index=False,
)

# 更新 session_state（確保日期仍是 date 類型）
st.session_state.projects = edited_df.copy()
st.session_state.projects["開始日期"] = pd.to_datetime(st.session_state.projects["開始日期"]).dt.date
st.session_state.projects["結束日期"] = pd.to_datetime(st.session_state.projects["結束日期"]).dt.date

# === 統計總覽 ===
st.markdown("### 📊 統計總覽")
col1, col2, col3, col4 = st.columns(4)
total_projects = len(edited_df)
in_progress = len(edited_df[edited_df["狀態"] == "進行中"])
total_budget = int(edited_df["預算 (萬)"].sum())
avg_progress = edited_df["進度 (%)"].mean()

with col1:
    st.metric("總專案數", total_projects)
with col2:
    st.metric("進行中專案", in_progress)
with col3:
    st.metric("總預算 (萬)", f"{total_budget:,}")
with col4:
    st.metric("平均進度", f"{avg_progress:.1f}%" if not pd.isna(avg_progress) else "0%")

# === 匯出功能 ===
st.download_button(
    label="📥 匯出為 CSV",
    data=edited_df.to_csv(index=False).encode('utf-8'),
    file_name=f"YIP_SHING_Projects_{datetime.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.caption("Powered by Streamlit | 資料即時儲存於 session（重啟會重置）。")