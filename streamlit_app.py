import streamlit as st
import pandas as pd
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="YIP SHING Project Database", layout="wide")
st.title("🗂️ YIP SHING Project Database")

# 初始化資料（只保留四個欄位）
if 'projects' not in st.session_state:
    st.session_state.projects = pd.DataFrame([
        {"Project ID": "YIP-001", "Customer": "客戶A公司", "負責人": "張三", "Lead Time": "60 天"},
        {"Project ID": "YIP-002", "Customer": "客戶B集團", "負責人": "李四", "Lead Time": "90 天"},
        {"Project ID": "YIP-003", "Customer": "客戶C科技", "負責人": "王五", "Lead Time": "45 天"},
    ])

df = st.session_state.projects.copy()

# === 側邊欄：新增 Project（只保留四個欄位）===
st.sidebar.header("📝 新增 Project")
with st.sidebar.form("add_project_form", clear_on_submit=True):
    st.write("### 填寫以下資訊新增專案")

    new_id = st.text_input("Project ID*", placeholder="例如: YIP-004", help="必填，唯一識別碼")
    new_customer = st.text_input("Customer*", placeholder="客戶名稱", help="必填")
    new_manager = st.text_input("負責人*", placeholder="負責人姓名", help="必填")
    new_leadtime = st.text_input("Lead Time*", placeholder="例如: 60 天 或 3 個月", help="必填，預計交付時間")

    submitted = st.form_submit_button("✨ 新增 Project")

    if submitted:
        if new_id and new_customer and new_manager and new_leadtime:
            # 檢查 Project ID 是否重複
            if new_id in df["Project ID"].values:
                st.error("❌ Project ID 已存在，請使用不同的 ID")
            else:
                new_row = pd.DataFrame([{
                    "Project ID": new_id,
                    "Customer": new_customer,
                    "負責人": new_manager,
                    "Lead Time": new_leadtime
                }])
                st.session_state.projects = pd.concat([st.session_state.projects, new_row], ignore_index=True)
                st.success(f"✅ 已成功新增 Project: {new_id}")
                st.rerun()
        else:
            st.error("❌ 請填寫所有必填欄位（標有 * 者）")

# === 主畫面：顯示與編輯表格（僅四欄）===
st.markdown("### 📋 Project 清單")

edited_df = st.data_editor(
    df,
    column_config={
        "Project ID": st.column_config.TextColumn("Project ID", disabled=True, help="ID 不可修改"),
        "Customer": st.column_config.TextColumn("Customer", required=True),
        "負責人": st.column_config.TextColumn("負責人", required=True),
        "Lead Time": st.column_config.TextColumn("Lead Time", required=True),
    },
    num_rows="dynamic",  # 允許直接在表格新增或刪除列
    use_container_width=True,
    hide_index=True,
)

# 更新資料
st.session_state.projects = edited_df

# === 統計資訊（簡化版）===
st.markdown("### 📊 總覽")
col1, col2 = st.columns(2)
with col1:
    st.metric("總 Project 數量", len(edited_df))
with col2:
    st.metric("不同客戶數", edited_df["Customer"].nunique())

# === 匯出 CSV ===
st.download_button(
    label="📥 匯出為 CSV",
    data=edited_df.to_csv(index=False).encode('utf-8'),
    file_name=f"YIP_SHING_Projects_{datetime.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# 底部說明
st.caption("Powered by Streamlit | 資料儲存於 session（重新部署會重置）")