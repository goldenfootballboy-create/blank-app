import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date

# ==============================================
# 1. 設定 + 純 JSON 永久儲存（超穩定）
# ==============================================
st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide", initial_sidebar_state="expanded")

PROJECTS_FILE = "projects_data.json"

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame(columns=["Project_Type", "Project_Name", "Year", "Lead_Time"])

    df = pd.DataFrame(data)
    for c in ["Project_Type", "Project_Name", "Year", "Lead_Time"]:
        if c not in df.columns: df[c] = None

    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce", downcast="integer").fillna(2025)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    return df


def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for c in date_cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


df = load_projects()

# ==============================================
# 2. 左側側邊欄：篩選 + 新增專案表單（都在左邊）
# ==============================================
with st.sidebar:
    st.title("Dashboard Controls")

    # ─── 新增專案表單（在左側）───
    with st.expander("新增專案", expanded=False):
        with st.form("add_form", clear_on_submit=True):
            st.write("### 填寫新專案資訊")
            c1, c2 = st.columns(2)
            with c1:
                new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
                new_name = st.text_input("Project Name*")
                new_year = st.selectbox("Year*", [2024, 2025, 2026], index=1)
                new_qty = st.number_input("Qty", min_value=1, value=1)
            with c2:
                new_customer = st.text_input("Customer")
                new_manager = st.text_input("負責人")
                new_leadtime = st.date_input("Lead Time*", value=date(2025, 12, 31))
                new_brand = st.text_input("Brand")

            new_desc = st.text_area("Description", height=80)

            if st.form_submit_button("新增專案"):
                if not new_name.strip():
                    st.error("Project Name 必填！")
                elif new_name in df["Project_Name"].values:
                    st.error("專案名稱重複！")
                else:
                    new_row = {
                        "Project_Type": new_type, "Project_Name": new_name, "Year": int(new_year),
                        "Lead_Time": new_leadtime.strftime("%Y-%m-%d"), "Customer": new_customer or "",
                        "負責人": new_manager or "", "Qty": new_qty, "Real_Count": new_qty,
                        "Brand": new_brand or "", "Description": new_desc or "",
                        "Parts_Arrival_Date": None, "Installation_Complete_Date": None,
                        "Testing_Date": None, "Cleaning": "", "Delivery_Date": None,
                        "Remarks": "", "Order_List": "", "Submit_List": "", "Progress_Tooltip": ""
                    }
                    df.loc[len(df)] = new_row
                    save_projects(df)
                    st.success(f"成功新增：{new_name}")
                    st.rerun()

    # ─── 篩選條件 ───
    st.markdown("---")
    st.subheader("篩選條件")

    # Project Type
    all_types = sorted(df["Project_Type"].dropna().unique().tolist())
    selected_type = st.selectbox("Project Type", ["All"] + all_types, index=0)

    # Year
    all_years = sorted(df["Year"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", all_years, index=all_years.index(2025) if 2025 in all_years else 0)

    # Lead Time Month
    month_options = ["All", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                     "十二月"]
    selected_month = st.selectbox("Lead Time Month", month_options, index=0)

# ==============================================
# 3. 篩選邏輯：Year + Lead Time Month 都要符合
# ==============================================
filtered_df = df[df["Year"] == selected_year].copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["Project_Type"] == selected_type]

if selected_month != "All":
    month_map = {"一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
                 "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12}
    m_num = month_map[selected_month]
    filtered_df = filtered_df[filtered_df["Lead_Time"].dt.month == m_num]

# ==============================================
# 4. 主畫面顯示（你原本的全部程式碼直接貼在這裡）
# ==============================================
st.markdown(f"### {selected_type} - {selected_year}年 {selected_month} 專案總覽")

if len(filtered_df) == 0:
    st.info("目前沒有符合條件的專案")
    st.stop()

# 下面直接貼上你原本從「統計」開始到「Memo Pad」結束的全部程式碼
# 只需要把所有原本的 df 改成 filtered_df 即可（你原本就這樣寫）

# 例如：
if 'Real_Count' in filtered_df.columns:
    total = int(filtered_df["Real_Count"].sum())
else:
    total = len(filtered_df)
st.write(f"**總數：{total}**")

# 把你原本的統計、進度條、延誤顯示、表格、Checklist、Memo 全部貼在這裡
# （我就不重複貼了，直接從你原本的程式碼複製過來即可）

st.caption("新增專案在左側展開 • 篩選 Year + Lead Time Month 會正確顯示該月份專案")