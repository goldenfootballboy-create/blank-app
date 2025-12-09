import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 1. 永久儲存 JSON（最穩版）
# ==============================================
PROJECTS_FILE = "projects_data.json"

# 若檔案不存在就建立空的
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # 安全轉日期
    if "Lead_Time" in df.columns:
        df["Lead_Time"] = pd.to_datetime(df["Lead_Time"], errors="coerce")
    if "Year" not in df.columns:
        df["Year"] = 2025
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    return df

def save_projects(df):
    df2 = df.copy()
    if "Lead_Time" in df2.columns:
        df2["Lead_Time"] = df2["Lead_Time"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else None
        )
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict("records"), f, ensure_ascii=False, indent=2)

# 載入所有專案
df = load_projects()

# ==============================================
# 2. 左側：新增專案表單
# ==============================================
with st.sidebar:
    st.header("新增專案")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_type = st.selectbox("Project Type*", ["Enclosure","Open Set","Scania","Marine","K50G3"])
            new_name = st.text_input("Project Name*", placeholder="例如：YIP-2025-001")
            new_year = st.selectbox("Year*", [2024,2025,2026], index=1)
            new_qty  = st.number_input("Qty", min_value=1, value=1)
        with col2:
            new_customer = st.text_input("Customer")
            new_manager  = st.text_input("負責人")
            new_leadtime = st.date_input("Lead Time*", value=date.today())
            new_brand    = st.text_input("Brand")

        new_desc = st.text_area("Description", height=100)

        if st.form_submit_button("新增專案", type="primary"):
            if not new_name.strip():
                st.error("專案名稱必填！")
            elif new_name in df["Project_Name"].values if len(df)>0 else False:
                st.error("專案名稱已存在！")
            else:
                new_project = {
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
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                st.success(f"已成功新增：{new_name}")
                st.rerun()

# ==============================================
# 3. 中間：顯示所有專案詳情（最簡單清晰版）
# ==============================================
st.title("YIP SHING 專案總覽")

if len(df) == 0:
    st.info("目前還沒有專案，請在左側新增第一筆專案")
else:
    # 顯示總數
    total = df["Real_Count"].sum() if "Real_Count" in df.columns else len(df)
    st.write(f"**目前共有 {int(total)} 個專案**")
    st.markdown("---")

    # 逐筆顯示專案卡片（美觀又清楚）
    for i, row in df.iterrows():
        with st.expander(f"**{row['Project_Name']}** • {row['Project_Type']} • {row.get('Customer','') or '無客戶'}", expanded=False):
            col1, col2 = st.columns([1,2])
            with col1:
                st.write(f"**年份：** {row['Year']}")
                st.write(f"**Lead Time：** {row['Lead_Time'].strftime('%Y-%m-%d') if pd.notna(row['Lead_Time']) else '未設定'}")
                st.write(f"**數量：** {row.get('Qty', '—')}")
                st.write(f"**負責人：** {row.get('負責人', '未指派')}")
            with col2:
                st.write(f"**Brand：** {row.get('Brand', '—')}")
                if row.get("Description"):
                    st.write(f"**說明：** {row['Description']}")

            st.markdown("---")

st.caption("所有專案已永久儲存於雲端 • 新增後立即顯示 • 不會遺失")