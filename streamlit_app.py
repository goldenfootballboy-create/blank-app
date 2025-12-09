import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# -------------------------------------------------
# 1. 基本設定 + 純 JSON 資料持久化
# -------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide", initial_sidebar_state="expanded")

# 永久儲存專案資料的檔案
PROJECTS_FILE = "projects_data.json"

# 初始資料（如果檔案不存在，就建立一個空的）
if not os.path.exists(PROJECTS_FILE):
    initial_data = []
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=2)
    st.info("已建立新的專案資料庫 `projects_data.json`，你可以開始新增專案！")


def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # 確保必要欄位存在
    required_cols = ['Project_Type', 'Project_Name', 'Year', 'Lead_Time']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    # 轉換日期欄位
    date_cols = ['Lead_Time', 'Parts_Arrival_Date', 'Installation_Complete_Date', 'Testing_Date', 'Delivery_Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(2025).astype(int)
    if 'Real_Count' not in df.columns:
        df['Real_Count'] = df.get('Qty', 1)

    return df


def save_projects(df):
    df_save = df.copy()
    date_cols = ['Lead_Time', 'Parts_Arrival_Date', 'Installation_Complete_Date', 'Testing_Date', 'Delivery_Date']
    for col in date_cols:
        if col in df_save.columns:
            df_save[col] = df_save[col].dt.strftime('%Y-%m-%d') if pd.notna(df_save[col]).any() else None
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df_save.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


# 載入專案資料
df = load_projects()

# -------------------------------------------------
# 2. 側邊欄：新增 Project + 篩選
# -------------------------------------------------
with st.sidebar:
    st.title("Dashboard Controls")

    # 新增專案表單
    with st.expander("➕ 新增 Project", expanded=False):
        with st.form("add_project_form", clear_on_submit=True):
            st.markdown("### 填寫新專案資訊")
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
                new_name = st.text_input("Project Name*", placeholder="例如: YIP-2025-001")
                new_year = st.selectbox("Year*", ["2024", "2025", "2026"], index=1)
                new_qty = st.number_input("Qty / Real_Count", min_value=1, value=1)
            with col2:
                new_customer = st.text_input("Customer (選填)")
                new_manager = st.text_input("負責人 (選填)")
                new_leadtime = st.date_input("Lead Time*", value=datetime(2025, 12, 31))
                new_brand = st.text_input("Brand (選填)")

            new_description = st.text_area("Description (選填)", height=80)

            submitted = st.form_submit_button("✨ 新增專案")
            if submitted:
                if not new_name:
                    st.error("Project Name 為必填！")
                elif new_name in df["Project_Name"].values:
                    st.error("此 Project Name 已存在！")
                else:
                    new_row = {
                        "Project_Type": new_type,
                        "Project_Name": new_name,
                        "Year": int(new_year),
                        "Lead_Time": new_leadtime.strftime('%Y-%m-%d'),
                        "Customer": new_customer or "",
                        "負責人": new_manager or "",
                        "Qty": new_qty,
                        "Real_Count": new_qty,
                        "Brand": new_brand or "",
                        "Description": new_description or "",
                        "Parts_Arrival_Date": None,
                        "Installation_Complete_Date": None,
                        "Testing_Date": None,
                        "Cleaning": "",
                        "Delivery_Date": None,
                        "Remarks": "",
                        "Order_List": "",
                        "Submit_List": "",
                        "Progress_Tooltip": ""
                    }
                    df.loc[len(df)] = new_row
                    save_projects(df)
                    st.success(f"✅ 已成功新增專案：{new_name}")
                    st.rerun()

    # 篩選控制
    st.markdown("### Project Type Selection")
    project_types = ["All", "Enclosure", "Open Set", "Scania", "Marine", "K50G3"]
    selected_project_type = st.selectbox("Select Project Type:", project_types, index=0)

    years = ["2024", "2025", "2026"]
    selected_year = st.selectbox("Select Year:", years, index=years.index("2025"))

    month_options = ["--", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                     "十二月"]
    selected_month = st.selectbox("Lead Time:", month_options, index=0)

# -------------------------------------------------
# 3. 你的完整 CSS + 標題（不變）
# -------------------------------------------------
st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #1fb429; margin-bottom: 1rem; margin-top: -4rem; font-weight: bold; display: flex; justify-content: center; align-items: center; width: 100%; }
    .main-header .title { flex-grow: 1; text-align: center; }
    /* ... 你原本的所有 CSS 全部貼上 ... */
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><div class="title">YIP SHING Project Status Dashboard</div></div>',
            unsafe_allow_html=True)
st.markdown("---")

# -------------------------------------------------
# 4. 篩選 + 統計 + 主畫面 + Checklist + Memo（你原本的全部保留）
# -------------------------------------------------
# 從這裡開始，直接貼上你原本程式碼中「篩選」到「Memo Pad」結束的所有內容
# 只需把所有 df 替換成我們上面載入的 df（已經是 JSON 的）

# 例如：
filtered_df = df[df['Year'] == int(selected_year)].copy()
# ... 其餘完全不變 ...

# （由於篇幅，我不重複貼你原本的 7~末尾程式碼，你直接從你上一個版本複製貼上即可）

st.caption("已完全改用 JSON 儲存 • 所有新增專案永久保留 • 無需 CSV")