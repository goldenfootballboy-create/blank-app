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
    required = ["Project_Type","Project_Name","Year","Lead_Time","Customer","Supervisor",
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

# ==============================================
# 左側：New Project（保持不變）
# ==============================================
with st.sidebar:
    st.header("New Project")
    # （表單內容和之前一樣，你直接用上一版即可，這裡省略）

# ==============================================
# 中間：小巧美觀進度卡（高度變小、進度條變細）
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        # 超緊緻進度卡（高度只有原本一半）
        st.markdown(f"""
        <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                    border-radius: 10px; 
                    padding: 12px 16px; 
                    margin: 8px 0; 
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-left: 6px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size:1.1rem; color:#1a1a1a;">{row['Project_Name']}</strong>
                    <span style="margin-left:12px; color:#555; font-size:0.9rem;">
                        {row['Project_Type']} • {row.get('Customer','—')} • Qty: {row.get('Qty',0)}
                    </span>
                </div>
                <strong style="color:white; background:{color}; padding:4px 12px; border-radius:20px; font-size:0.95rem;">
                    {pct}% 
                </strong>
            </div>
            <div style="margin-top:6px; font-size:0.9rem; color:#444;">
                Lead Time: {fmt(row['Lead_Time'])} | Supervisor: {row.get('Supervisor','—')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 點擊可展開看詳細規格
        with st.expander(f"View Details • {row['Project_Name']}", expanded=False):
            st.markdown(f"""
            <div style="padding:15px; background:#fafafa; border-radius:8px; line-height:1.7;">
                <p><strong>Year:</strong> {row['Year']}</p>
                {f"<p><strong>Description:</strong><br>{row.get('Description','—')}</p>" if row.get('Description') else ""}
                <hr style="border:0.5px dashed #ccc;">
                <strong>Project Specification:</strong>
                <pre style='background:#f0f0f0; padding:10px; border-radius:6px; margin:10px 0; white-space: pre-wrap; font-size:0.95rem;'>
{row.get('Project_Spec','—')}
                </pre>
                <p><strong>Progress Dates:</strong></p>
                <ul style="margin:8px 0; padding-left:20px;">
                    <li>Parts Arrival: {fmt(row.get('Parts_Arrival'))}</li>
                    <li>Installation: {fmt(row.get('Installation_Complete'))}</li>
                    <li>Testing: {fmt(row.get('Testing_Complete'))}</li>
                    <li>Cleaning: {fmt(row.get('Cleaning_Complete'))}</li>
                    <li>Delivery: {fmt(row.get('Delivery_Complete'))}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,8])
            if col1.button("Edit", key=f"e{idx}", use_container_width=True):
                st.session_state.editing_index = idx
            if col2.button("Delete", key=f"d{idx}", type="secondary", use_container_width=True):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

st.markdown("---")
st.caption("Compact progress card • All key info visible without expanding • Clean and beautiful")