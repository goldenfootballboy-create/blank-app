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
    required = ["Project_Type","Project_Name","Year","Lead_Time","Customer","Customer","Supervisor",
                "Qty","Real_Count","Project_Spec","Description",
                "Parts_Arrival","Installation_Complete","Testing_Complete","Cleaning_Complete","Delivery_Complete"]
    for c in required:
        if c not in df.columns: df[c] = None
    date_cols = ["Lead_Time","Parts_Arrival","Installation_Complete","Testing_Complete","Cleaning_Complete","Delivery_Complete"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(2025).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    return df

def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time","Parts_Arrival","Installation_Complete","Testing_Complete","Cleaning_Complete","Delivery_Complete"]
    for c in date_cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else None)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict("records"), f, ensure_ascii=False, indent=2)

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
    if pct >= 100: return "#0066ff"
    elif pct >= 90: return "#00aa00"
    elif pct >= 70: return "#66cc66"
    elif pct >= 30: return "#ffaa00"
    else: return "#ff4444"

def fmt(d):
    return pd.to_datetime(d).strftime("%Y-%m-%d") if pd.notna(d) else "—"

# ==============================================
# 左側：New Project（保持不變）
# ==============================================
with st.sidebar:
    st.header("New Project")
    # （表單內容和之前一樣，我就不重複貼了，你用上一版的即可）

# ==============================================
# 中間：夢幻彩色進度卡（不用展開就全部看到！）
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        # 整張卡片就是進度條 + 內容一體成型
        st.markdown(f"""
        <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                    border-radius: 8px; 
                    padding: 2px; 
                    margin: 12px 0; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    border-left: 8px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin:0; color:white; text-shadow: 1px 1px 3px rgba(0,0,0,0.6);">
                    {row['Project_Name']} • {row['Project_Type']}
                </h3>
                <span style="color:white; font-weight:bold; font-size:1.4rem; text-shadow: 1px 1px 3px rgba(0,0,0,0.8);">
                    {pct}% Complete
                </span>
            </div>
            <div style="margin-top:10px; color:#333;">
                <strong>Customer:</strong> {row.get('Customer','—')} | 
                <strong>Supervisor:</strong> {row.get('Supervisor','—')} | 
                <strong>Qty:</strong> {row.get('Qty',0)} | 
                <strong>Lead Time:</strong> {fmt(row['Lead_Time'])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 點擊卡片下方可展開看詳細規格（可選）
        with st.expander(f"View Details • {row['Project_Name']}", expanded=False):
            st.markdown(f"""
            <div style="padding:15px; background:#fafafa; border-radius:8px;">
                <p><strong>Year:</strong> {row['Year']}</p>
                <p><strong>Description:</strong><br>{row.get('Description','—')}</p>
                <hr>
                <strong>Project Specification:</strong>
                <pre style="background:#f0f0f0; padding:12px; border-radius:6px; white-space: pre-wrap; margin:10px 0;">
{row.get('Project_Spec','—')}
                </pre>
                <p><strong>Progress Dates:</strong></p>
                <ul>
                    <li>Parts Arrival: {fmt(row.get('Parts_Arrival'))}</li>
                    <li>Installation: {fmt(row.get('Installation_Complete'))}</li>
                    <li>Testing: {fmt(row.get('Testing_Complete'))}</li>
                    <li>Cleaning: {fmt(row.get('Cleaning_Complete'))}</li>
                    <li>Delivery: {fmt(row.get('Delivery_Complete'))}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            col_btn = st.columns([1,1,8])[0]
            if col_btn.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.editing_index = idx
            if col_btn.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

# 其餘 Edit 功能保持不變（可沿用上一版）

st.markdown("---")
st.caption("Progress bar integrated into card • Key info visible without expanding • Color indicates progress at a glance • Perfect for both light/dark themes")