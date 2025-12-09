import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# 頁面設定
st.set_page_config(page_title="YIP SHING Project Database", layout="wide")
st.title("🗂️ YIP SHING Project Database")

# 初始化資料（統一欄位名稱）
if 'projects' not in st.session_state:
    st.session_state.projects = pd.DataFrame([
        {"Project ID": "YIP-001", "Customer": "客戶A公司", "負責人": "張三", "預計交付日期": date(2026, 2, 15)},
        {"Project ID": "YIP-002", "Customer": "客戶B集團", "負責人": "李四", "預計交付日期": date(2026, 4, 1)},
        {"Project ID": "YIP-003", "Customer": "客戶C科技", "負責人": "王五", "預計交付日期": date(2026, 1, 20)},
    ])

df = st.session_state.projects.copy()

# 確保日期欄位為 date 類型（安全轉換）
if "預計交付日期" in df.columns:
    df["預計交付日期"] = pd.to_datetime(df["預計交付日期"], errors='coerce').dt.date

# === 側邊欄：新增 Project ===
st.sidebar.header("📝 新增 Project")
with st.sidebar.form("add_project_form", clear_on_submit=True):
    st.write("### 填寫以下資訊新增專案")

    new_id = st.text_input("Project ID*", placeholder="例如: YIP-004", help="必填，唯一識別碼")
    new_customer = st.text_input("Customer*", placeholder="客戶名稱", help="必填")
    new_manager = st.text_input("負責人*", placeholder="負責人姓名", help="必填")

    # 日歷選擇預計交付日期
    new_leadtime_date = st.date_input(
        "預計交付日期 (Lead Time)*",
        value=date.today() + timedelta(days=60),  # 預設 60 天後
        min_value=date.today(),
        help="點擊日歷選擇預計交付日期"
    )

    submitted = st.form_submit_button("✨ 新增 Project")

    if submitted:
        if new_id and new_customer and new_manager:
            if new_id in df["Project ID"].values:
                st.error("❌ Project ID 已存在，請使用不同的 ID")
            else:
                lead_days = (new_leadtime_date - date.today()).days
                new_row = pd.DataFrame([{
                    "Project ID": new_id,
                    "Customer": new_customer,
                    "負責人": new_manager,
                    "預計交付日期": new_leadtime_date  # 直接存 date
                }])
                st.session_state.projects = pd.concat([st.session_state.projects, new_row], ignore_index=True)
                st.success(f"✅ 已成功新增 Project: {new_id}\n\n預計交付日期：{new_leadtime_date}（距今日 {lead_days} 天）")
                st.rerun()
        else:
            st.error("❌ 請填寫所有必填欄位（標有 * 者）")

# === 主畫面：顯示與編輯表格 ===
st.markdown("### 📋 Project 清單")

# 計算剩餘天數（用於顯示）
display_df = df.copy()
today = date.today()
display_df["剩餘天數"] = display_df["預計交付日期"].apply(
    lambda x: f"{(x - today).days} 天" if (x - today).days >= 0 else f"已逾期 {-(x - today).days} 天"
)

edited_df = st.data_editor(
    display_df,
    column_config={
        "Project ID": st.column_config.TextColumn("Project ID", disabled=True),
        "Customer": st.column_config.TextColumn("Customer", required=True),
        "負責人": st.column_config.TextColumn("負責人", required=True),
        "預計交付日期": st.column_config.DateColumn(
            "預計交付日期 (Lead Time)",
            min_value=date.today() - timedelta(days=365),
            max_value=date.today() + timedelta(days=365 * 2),
            format="YYYY-MM-DD",
            required=True
        ),
        "剩餘天數": st.column_config.TextColumn("剩餘天數", disabled=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_order=["Project ID", "Customer", "負責人", "預計交付日期", "剩餘天數"]
)

# 更新原始資料（移除輔助欄位）
updated_projects = edited_df.drop(columns=["剩餘天數"], errors="ignore")
st.session_state.projects = updated_projects[["Project ID", "Customer", "負責人", "預計交付日期"]].copy()

# === 統計總覽 ===
st.markdown("### 📊 總覽")
col1, col2, col3 = st.columns(3)
total = len(edited_df)

# 計算進行中與逾期
on_time_count = 0
overdue_count = 0
for days_str in edited_df["剩餘天數"]:
    if "逾期" in days_str:
        overdue_count += 1
    elif "天" in days_str:
        days = int(days_str.split()[0])
        if days >= 0:
            on_time_count += 1

with col1:
    st.metric("總 Project 數量", total)
with col2:
    st.metric("進行中 / 即將到期", on_time_count)
with col3:
    st.metric("已逾期", overdue_count, delta_color="inverse")

# === 匯出 CSV ===
st.download_button(
    label="📥 匯出為 CSV",
    data=edited_df.to_csv(index=False).encode('utf-8'),
    file_name=f"YIP_SHING_Projects_{date.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.caption("Powered by Streamlit | 預計交付日期可點擊日歷選擇 • 目前日期：2025-12-09")