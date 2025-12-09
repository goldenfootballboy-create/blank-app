import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date

# ==============================================
# 1. 設定 + JSON 永久儲存（超穩定版）
# ==============================================
st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide", initial_sidebar_state="expanded")

PROJECTS_FILE = "projects_data.json"

# 若檔案不存在就建立空的
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame(columns=["Project_Type", "Project_Name", "Year", "Lead_Time"])

    df = pd.DataFrame(data)

    # 補齊必要欄位
    for col in ["Project_Type", "Project_Name", "Year", "Lead_Time"]:
        if col not in df.columns:
            df[col] = None

    # 日期欄位安全轉換
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce", downcast="integer").fillna(2025)

    # 修正這一行（原本打錯了）
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
# 2. 左側側邊欄 → 只放篩選（超乾淨）
# ==============================================
with st.sidebar:
    st.title("篩選條件")

    # 動態產生選項
    all_types = sorted(df["Project_Type"].dropna().unique().tolist())
    project_types = ["All"] + all_types
    selected_type = st.selectbox("Project Type", project_types, index=0)

    all_years = sorted(df["Year"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", all_years, index=all_years.index(2025) if 2025 in all_years else 0)

    month_options = ["All", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                     "十二月"]
    selected_month = st.selectbox("Lead Time Month", month_options, index=0)

# ==============================================
# 3. 主畫面頂端：新增專案按鈕 + 表單在中間顯示
# ==============================================
col_add, col_space = st.columns([2, 8])
with col_add:
    if st.button("新增專案", type="primary", use_container_width=True):
        st.session_state.show_add_form = True

# 表單只在中間顯示
if st.session_state.get("show_add_form", False):
    st.markdown("---")
    st.subheader("新增專案")
    with st.form("add_project_main", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
            new_name = st.text_input("Project Name*", placeholder="例如：YIP-2025-099")
            new_year = st.selectbox("Year*", [2024, 2025, 2026], index=1)
            new_qty = st.number_input("Qty", min_value=1, value=1)
        with c2:
            new_customer = st.text_input("Customer（選填）")
            new_manager = st.text_input("負責人（選填）")
            new_leadtime = st.date_input("Lead Time*", value=date.today())
            new_brand = st.text_input("Brand（選填）")
        new_desc = st.text_area("Description（選填）", height=100)

        col_sub, col_can = st.columns([1, 8])
        with col_sub:
            submitted = st.form_submit_button("確認新增", type="primary")
        with col_can:
            if st.form_submit_button("取消"):
                del st.session_state.show_add_form
                st.rerun()

        if submitted:
            if not new_name.strip():
                st.error("Project Name 必填！")
            elif new_name in df["Project_Name"].values:
                st.error("此專案名稱已存在！")
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
                df.loc[len(df)] = new_row
                save_projects(df)
                st.success(f"成功新增專案：{new_name}")
                del st.session_state.show_add_form
                st.rerun()

# ==============================================
# 4. 篩選後的資料
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
# 5. 以下直接貼上你原本從「統計」開始到「Memo Pad」結束的所有程式碼
#    只要把所有出現的 df 改成 filtered_df 即可（你原本就這樣寫）
# ==============================================
# 例如：
st.markdown(f"### {selected_type} - {selected_year} 年 {selected_month} 專案總覽")
if 'Real_Count' in filtered_df.columns:
    total = int(filtered_df["Real_Count"].sum())
else:
    total = len(filtered_df)
st.write(f"**總數：{total}**")

# 然後把你原本的統計、進度條、延誤顯示、表格、Checklist、Memo 全部貼在這裡
# （我就不重複貼了，你直接從你原本程式碼複製過來即可）

st.caption("點上方「新增專案」按鈕 → 表單在中間顯示 → 送出後立即出現在清單")