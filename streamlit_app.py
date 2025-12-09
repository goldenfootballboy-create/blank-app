import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 永久儲存 + 完全防呆
# ==============================================
PROJECTS_FILE = "projects_data.json"

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for c in ["Project_Type","Project_Name","Year","Lead_Time"]:
        if c not in df.columns: df[c] = None
    date_cols = ["Lead_Time","Parts_Arrival_Date","Installation_Complete_Date","Testing_Date","Delivery_Date"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(2025).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = 1
    return df

def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time","Parts_Arrival_Date","Installation_Complete_Date","Testing_Date","Delivery_Date"]
    for c in date_cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else None)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

df = load_projects()

# ==============================================
# 左側：新增專案（唯一入口）
# ==============================================
with st.sidebar:
    st.title("新增專案")

    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_type = st.selectbox("Project Type*", ["Enclosure","Open Set","Scania","Marine","K50G3"])
            new_name = st.text_input("Project Name*")
            new_year = st.selectbox("Year*", [2024,2025,2026], index=1)
            new_qty  = st.number_input("Qty", min_value=1, value=1)
        with c2:
            new_customer = st.text_input("Customer")
            new_manager  = st.text_input("負責人")
            new_leadtime = st.date_input("Lead Time*", value=date.today())
            new_brand    = st.text_input("Brand")
        new_desc = st.text_area("Description", height=80)

        if st.form_submit_button("新增專案", type="primary", use_container_width=True):
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
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_projects(df)
                st.success(f"成功新增：{new_name}")
                st.rerun()

# ==============================================
# 主畫面：自動顯示「最新新增專案的同年同月」專案
# ==============================================
if len(df) == 0:
    st.info("尚未有任何專案，請先在左側新增")
    st.stop()

# 安全取得最新一筆的年月（絕對不會出錯）
latest_row = df.iloc[-1]
latest_year = int(latest_row["Year"])

# 安全處理 Lead_Time（如果為 None 或 NaT，就用今天）
if pd.isna(latest_row["Lead_Time"]):
    latest_leadtime = date.today()
else:
    latest_leadtime = pd.to_datetime(latest_row["Lead_Time"])

latest_month = latest_leadtime.month

# 篩選
filtered_df = df[
    (df["Year"] == latest_year) &
    (df["Lead_Time"].dt.month == latest_month)
].copy()

# 中文月份
month_names = ["", "一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]
current_month_name = month_names[latest_month]

# ==============================================
# 主畫面標題
# ==============================================
st.markdown(f"# {latest_year}年 {current_month_name} 專案總覽")
st.markdown("**自動顯示與最新新增專案同年同月的全部專案**")

if len(filtered_df) == 0:
    st.info("這個月還沒有專案")
else:
    # 這裡貼上你原本從統計開始到 Memo 結束的所有程式碼
    # 把所有 df 改成 filtered_df 即可
    total = int(filtered_df["Real_Count"].sum()) if "Real_Count" in filtered_df.columns else len(filtered_df)
    st.write(f"**本月專案總數：{total}**")

    # 把你原本整段進度條、延誤、表格、Checklist、Memo 全部貼在這裡
    # （你直接複製貼上就行）

st.markdown("---")
st.caption("每次新增專案後，系統自動切換顯示同年同月全部專案")