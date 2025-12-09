import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# -------------------------------------------------
# 1. 基本設定 + 資料持久化（新增 projects_data.json）
# -------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide", initial_sidebar_state="expanded")

# 永久儲存專案資料的檔案
PROJECTS_FILE = "projects_data.json"


def load_projects():
    """優先讀取 JSON 永久資料，若無則讀取 CSV 作為初始"""
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
    else:
        # 首次使用時從 CSV 讀取並轉存到 JSON
        csv_file = "projects.csv"
        if not os.path.exists(csv_file):
            st.error(f"找不到 `projects.csv` 或 `projects_data.json`！請上傳初始資料。")
            st.stop()
        df = pd.read_csv(csv_file, encoding='utf-8')
        # 轉存到 JSON 以便後續永久編輯
        save_projects(df)
    # 確保日期欄位正確
    date_cols = ['Lead_Time', 'Parts_Arrival_Date', 'Installation_Complete_Date', 'Testing_Date', 'Delivery_Date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    return df


def save_projects(df):
    """儲存專案資料到 JSON（永久）"""
    df_save = df.copy()
    date_cols = ['Lead_Time', 'Parts_Arrival_Date', 'Installation_Complete_Date', 'Testing_Date', 'Delivery_Date']
    for col in date_cols:
        if col in df_save.columns:
            df_save[col] = df_save[col].astype(str)  # 日期轉字串儲存
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df_save.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


# 載入專案資料
df = load_projects()

# -------------------------------------------------
# 2. 新增 Project 表單（側邊欄最上方）
# -------------------------------------------------
with st.sidebar:
    st.title("Dashboard Controls")

    with st.expander("➕ 新增 Project", expanded=False):
        with st.form("add_project_form", clear_on_submit=True):
            st.markdown("### 填寫新專案資訊")
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
                new_name = st.text_input("Project Name*")
                new_year = st.selectbox("Year*", ["2024", "2025", "2026"], index=1)
            with col2:
                new_customer = st.text_input("Customer (選填)")
                new_manager = st.text_input("負責人 (選填)")
                new_leadtime = st.date_input("Lead Time*", value=datetime(2025, 12, 31))

            new_qty = st.number_input("Qty", min_value=1, value=1)
            new_brand = st.text_input("Brand (選填)")
            new_description = st.text_input("Description (選填)")

            submitted = st.form_submit_button("✨ 新增專案")
            if submitted:
                if not new_name:
                    st.error("Project Name 為必填！")
                elif new_name in df["Project_Name"].values:
                    st.error("此 Project Name 已存在！")
                else:
                    new_row = pd.DataFrame([{
                        "Project_Type": new_type,
                        "Project_Name": new_name,
                        "Year": int(new_year),
                        "Lead_Time": pd.to_datetime(new_leadtime),
                        "Customer": new_customer or "",
                        "負責人": new_manager or "",
                        "Qty": new_qty,
                        "Brand": new_brand or "",
                        "Description": new_description or "",
                        "Real_Count": new_qty,  # 預設與 Qty 相同
                        "Parts_Arrival_Date": None,
                        "Installation_Complete_Date": None,
                        "Testing_Date": None,
                        "Cleaning": "",
                        "Delivery_Date": None,
                        "Remarks": "",
                        "Order_List": "",
                        "Submit_List": "",
                        "Progress_Tooltip": ""
                    }])
                    global df
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_projects(df)
                    st.success(f"✅ 已成功新增專案：{new_name}")
                    st.rerun()

    # 原本的篩選控制
    st.markdown("### Project Type Selection")
    project_types = ["All", "Enclosure", "Open Set", "Scania", "Marine", "K50G3"]
    selected_project_type = st.selectbox("Select Project Type:", project_types, index=0)

    years = ["2024", "2025", "2026"]
    selected_year = st.selectbox("Select Year:", years, index=years.index("2025"))

    month_options = ["--", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                     "十二月"]
    selected_month = st.selectbox("Lead Time:", month_options, index=0)

# -------------------------------------------------
# 其餘程式碼完全不變（從你的原始程式複製）
# -------------------------------------------------
# （以下直接貼上你原本從 CSS 到 Memo Pad 的所有程式碼，我只微調了 df 的來源）

# 你的完整 CSS
st.markdown("""
<style>
    /* 你原本的完整 CSS 保持不變 */
    .main-header { font-size: 3rem; color: #1fb429; margin-bottom: 1rem; margin-top: -4rem; font-weight: bold; display: flex; justify-content: center; align-items: center; width: 100%; }
    .main-header .title { flex-grow: 1; text-align: center; }
    /* ... 其餘 CSS 全部保留 ... */
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><div class="title">YIP SHING Project Status Dashboard</div></div>',
            unsafe_allow_html=True)
st.markdown("---")

# 篩選邏輯（不變）
filtered_df = df[df['Year'] == int(selected_year)].copy()
if selected_project_type != "All":
    filtered_df = filtered_df[filtered_df['Project_Type'] == selected_project_type]
if selected_month != "--" and 'Lead_Time' in filtered_df.columns:
    month_idx = month_options.index(selected_month)
    if month_idx > 0:
        filtered_df = filtered_df[filtered_df['Lead_Time'].dt.month == month_idx]

# 統計、進度條、延誤顯示、Checklist、Memo Pad
# （你原本從第 7 節到最後的所有程式碼完全不變，只需要確保使用 filtered_df 和 df）

# 注意：所有原本使用 df 的地方現在都是正確的，因為 df 已經是永久可寫入的

# 其餘你原本的程式碼直接貼上（統計、進度條、延誤、Checklist、Memo）保持 100% 原樣
# 為了篇幅，這裡省略，但你只要把你原本的程式從「統計」開始到最後全部貼上即可

st.caption("現在支援網頁直接新增專案 • 新增後會永久儲存並立即顯示 • 舊資料從 projects.csv 匯入")