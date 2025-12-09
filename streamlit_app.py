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

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    for c in ["Project_Type","Project_Name","Year","Lead_Time"]:
        if c not in df.columns: df[c] = None
    date_cols = ["Lead_Time","Parts_Arrival_Date","Installation_Complete_Date","Testing_Date","Delivery_Date"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce", downcast="integer").fillna(2025)
    if "Real_Count"Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    return df

def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time","Parts_Arrival_Date","Installation_Complete_Date","Testing_Date","Delivery_Date"]
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
    project_types = ["All"] + sorted(df["Project_Type"].dropna().unique().tolist())
    selected_type = st.selectbox("Project Type", project_types, index=0)

    years = sorted(df["Year"].dropna().unique().tolist())
    selected_year = st.selectbox("Year", years, index=years.index(2025) if 2025 in years else 0)

    month_options = ["All"] + ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]
    selected_month = st.selectbox("Lead Time Month", month_options, index=0)

# ==============================================
# 3. 主畫面頂端：新增專案按鈕 + 表單（只在主畫面跳出）
# ==============================================
col_btn, col_space = st.columns([1, 8])
with col_btn:
    if st.button("新增專案", type="primary", use_container_width=True):
        st.session_state.show_add_form = True

# 顯示新增表單（在主畫面中間）
if st.session_state.get("show_add_form", False):
    with st.form("main_add_form", clear_on_submit=True):
        st.markdown("### 新增專案")
        c1, c2 = st.columns(2)
        with c1:
            new_type = st.selectbox("Project Type*", ["Enclosure","Open Set","Scania","Marine","K50G3"], key="m_type")
            new_name = st.text_input("Project Name*", key="m_name")
            new_year = st.selectbox("Year*", [2024,2025,2026], index=1, key="m_year")
            new_qty  = st.number_input("Qty", min_value=1, value=1, key="m_qty")
        with c2:
            new_customer = st.text_input("Customer", key="m_cust")
            new_manager  = st.text_input("負責人", key="m_mgr")
            new_leadtime = st.date_input("Lead Time*", value=date.today(), key="m_lead")
            new_brand    = st.text_input("Brand", key="m_brand")
        new_desc = st.text_area("Description", height=100, key="m_desc")

        col_sub, col_can = st.columns([1,8])
        with col_sub:
            submitted = st.form_submit_button("確認新增", type="primary")
        with col_can:
            if st.form_submit_button("取消"):
                st.session_state.show_add_form = False
                st.rerun()

        if submitted:
            if not new_name.strip():
                st.error("專案名稱必填！")
            elif new_name in df["Project_Name"].values:
                st.error("專案名稱已存在！")
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
                st.success(f"成功新增專案：{new_name}")
                st.session_state.show_add_form = False
                st.rerun()

# ==============================================
# 4. 篩選邏輯
# ==============================================
filtered_df = df[df["Year"] == selected_year].copy()

if selected_type != "All":
    filtered_df = filtered_df[filtered_df["Project_Type"] == selected_type]

if selected_month != "All":
    month_map = {"一月":1,"二月":2,"三月":3,"四月":4,"五月":5,"六月":6,"七月":7,"八月":8,"九月":9,"十月":10,"十一月":11,"十二月":12}
    m_num = month_map[selected_month]
    filtered_df = filtered_df[filtered_df["Lead_Time"].dt.month == m_num]

# ==============================================
# 5. 這裡開始貼你原本的「統計 + 進度條 + 延誤 + 表格 + Checklist + Memo」全部程式碼
# ==============================================
# 你只要把原本從「統計」開始到程式結尾的所有程式碼貼在這裡即可
# 只需要把所有的 df 改成 filtered_df（你原本就這樣寫）

# 例如：
st.markdown("### 專案統計")
total = filtered_df["Real_Count"].sum() if "Real_Count" in filtered_df.columns else 0
st.write(f"**總數：{int(total)}**")

# 然後把你原本的進度條、延誤、表格、Checklist、Memo 全部貼上來
# （因為太長就不重複貼了，你直接從你原本的程式複製貼上來即可）

st.caption("新增專案請點上方「新增專案」按鈕 → 表單在中間顯示 → 送出後立即出現在清單")
