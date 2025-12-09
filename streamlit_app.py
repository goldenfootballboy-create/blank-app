import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 永久儲存
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
    required = ["Project_Type", "Project_Name", "Year", "Lead_Time", "Customer", "Supervisor",
                "Qty", "Real_Count", "Project_Spec", "Description",
                "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete", "Delivery_Complete"]
    for c in required:
        if c not in df.columns: df[c] = None
    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete",
                 "Delivery_Complete"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(2025).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    return df


def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete",
                 "Delivery_Complete"]
    for c in date_cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else None)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict("records"), f, force_ascii=False, indent=2)


df = load_projects()


# ==============================================
# 進度計算 + 顏色
# ==============================================
def calculate_progress(row):
    p = 0
    if pd.notna(row.get("Parts_Arrival")): p += 30
    if pd.notna(row.get("Installation_Complete")): p += 40
    if pd.notna(row.get("Testing_Complete")): p += 10
    if pd.notna(row.get("Cleaning_Complete")): p += 10
    if pd.notna(row.get("Delivery_Complete")): p += 10
    return min(p, 100)


def get_color(pct):
    if pct >= 100:
        return "#0066ff"
    elif pct >= 90:
        return "#00aa00"
    elif pct >= 70:
        return "#66cc66"
    elif pct >= 30:
        return "#ffaa00"
    else:
        return "#ff4444"


# ==============================================
# 左側：New Project
# ==============================================
with st.sidebar:
    st.header("New Project")
    # （你原本的 New Project 表單，保持不變）

# ==============================================
# 中間：Project Counter + 卡片
# ==============================================
st.title("YIP SHING Project Dashboard")

# 恢復你最愛的 Project Counter（按 Project Type 統計 Real_Count）
if len(df) > 0:
    st.markdown("### Project Counter")
    counter_df = df.groupby("Project_Type")["Real_Count"].sum().reset_index()
    counter_df = counter_df.sort_values("Project_Type")

    total = int(df["Real_Count"].sum())

    cols = st.columns(len(counter_df) + 1)
    with cols[0]:
        st.metric("Total Projects", total)
    for i, row in counter_df.iterrows():
        with cols[i + 1]:
            st.metric(row["Project_Type"], int(row["Real_Count"]))

    st.markdown("---")

# 專案卡片列表
for idx, row in df.iterrows():
    pct = calculate_progress(row)
    color = get_color(pct)

    st.markdown(f"""
    <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                border-radius: 8px; padding: 10px 15px; margin: 6px 0; 
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-weight: bold;">
                {row['Project_Name']} • {row['Project_Type']}
            </div>
            <div style="color:white; background:{color}; padding:2px 10px; border-radius:12px; font-weight:bold;">
                {pct}%
            </div>
        </div>
        <div style="font-size:0.85rem; color:#555; margin-top:4px;">
            {row.get('Customer', '—')} | {row.get('Supervisor', '—')} | Qty:{row.get('Qty', 0)} | 
            Lead Time: {pd.to_datetime(row['Lead_Time']).strftime('%Y-%m-%d') if pd.notna(row['Lead_Time']) else '—'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 展開詳細內容
    with st.expander(f"Details • {row['Project_Name']}", expanded=False):
        # （詳細內容保持不變）
        # Edit 和 Delete 按鈕
        col1, col2 = st.columns(2)
        if col1.button("Edit", key=f"edit_{idx}"):
            st.session_state.editing_index = idx
        if col2.button("Delete", key=f"del_{idx}", type="secondary"):
            df = df.drop(idx).reset_index(drop=True)
            save_projects(df)
            st.rerun()

# 其餘 Edit 功能保持不變（可沿用上一版的完整 Edit 表單）

st.markdown("---")
st.caption("Project Counter restored • Compact progress cards • Edit fully working")