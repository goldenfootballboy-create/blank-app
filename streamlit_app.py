import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 1. 永久儲存 JSON（超級防呆版）
# ==============================================
PROJECTS_FILE = "projects_data.json"

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # 必要欄位補齊
    for col in ["Project_Type", "Project_Name", "Year", "Lead_Time"]:
        if col not in df.columns:
            df[col] = None

    # 安全轉日期（完全不會出錯）
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")  # 直接轉，壞的變 NaT

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(2025).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = pd.to_numeric(df["Real_Count"], errors="coerce").fillna(1).astype(int)
    else:
        df["Real_Count"] = 1
    return df


# 完全安全的儲存函數（這次絕對不會再出 .strftime 錯）
def save_projects(df):
    df_save = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for col in date_cols:
        if col in df_save.columns:
            # 只對真正的 datetime 才轉字串，其他直接變 None
            df_save[col] = df_save[col].apply(
                lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (pd.Timestamp, date)) and pd.notna(x) else None
            )
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df_save.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


df = load_projects()

# ==============================================
# 2. 左側側邊欄（篩選 + 新增都在左邊）
# ==============================================
with st.sidebar:
    st.title("Dashboard Controls")

    # 新增專案
    with st.expander("新增專案", expanded=False):
        with st.form("add_form", clear_on_submit=True):
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
                    st.error("專案名稱必填")
                elif new_name in df["Project_Name"].values:
                    st.error("專案名稱已存在")
                else:
                    new_row = {
                        "Project_Type": new_type,
                        "Project_Name": new_name,
                        "Year": int(new_year),
                        "Lead_Time": new_leadtime.strftime("%Y-%m-%d"),
                        "Customer": new_customer or "",
                        "負責人": new_manager or "",
                        "Qty": new_qty,
                        "Real_Count": new_qty,
                        "Brand": new_brand or "",
                        "Description": new_desc or "",
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
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_projects(df)
                    st.success(f"已新增：{new_name}")
                    st.rerun()

    st.markdown("---")
    st.subheader("篩選條件")

    types = ["All"] + sorted(df["Project_Type"].dropna().unique().tolist())
    selected_type = st.selectbox("Project Type", types, index=0)

    years = sorted(df["Year"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", years, index=years.index(2025) if 2025 in years else 0)

    months = ["All", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]
    selected_month = st.selectbox("Lead Time Month", months, index=0)

# ==============================================
# 3. 篩選：Year + Lead Time Month 同時符合
# ==============================================
filtered_df = df[df["Year"] == selected_year].copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["Project_Type"] == selected_type]

if selected_month != "All":
    month_num = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                 "十二月"].index(selected_month) + 1
    filtered_df = filtered_df[filtered_df["Lead_Time"].dt.month == month_num]

# ==============================================
# 4. 主畫面顯示（直接貼你原本的程式碼）
# ==============================================
st.markdown(f"### {selected_type} - {selected_year}年 {selected_month} 專案列表")

if len(filtered_df) == 0:
    st.info("沒有符合條件的專案")
else:
    # 這裡開始貼上你原本從「統計」到「Memo Pad」結束的所有程式碼
    # 只需要把原本的 df 全部換成 filtered_df 即可
    # 你原本的進度條、延誤、表格、Checklist、Memo 全部照搬過來就行

    # 範例（你原本的開頭）：
    total = int(filtered_df["Real_Count"].sum()) if "Real_Count" in filtered_df.columns else len(filtered_df)
    st.write(f"**總數：{total}**")

    # 之後把你原本整段漂亮的排版全部貼在這裡

st.caption("新增專案在左側 • 同時選 Year + Lead Time Month 會正確篩選該月份專案 • 所有資料永久儲存")