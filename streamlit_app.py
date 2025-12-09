import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 永久儲存 JSON
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
    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete",
                 "Delivery_Complete"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    if "Year" not in df.columns:
        df["Year"] = 2025
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    if "Project_Spec" not in df.columns:
        df["Project_Spec"] = ""
    return df


def save_projects(df):
    df2 = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete",
                 "Delivery_Complete"]
    for c in date_cols:
        if c in df2.columns:
            df2[c] = df2[c].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else None)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict("records"), f, ensure_ascii=False, indent=2)


df = load_projects()


# ==============================================
# 計算進度百分比
# ==============================================
def calculate_progress(row):
    progress = 0
    today = date.today()
    if pd.notna(row["Parts_Arrival"]): progress += 30
    if pd.notna(row["Installation_Complete"]): progress += 40
    if pd.notna(row["Testing_Complete"]): progress += 10
    if pd.notna(row["Cleaning_Complete"]): progress += 10
    if pd.notna(row["Delivery_Complete"]): progress += 10
    return min(progress, 100)


def get_progress_color(pct):
    if pct >= 100:
        return "#0066ff"  # 藍色（完成）
    elif pct >= 90:
        return "#00aa00"  # 深綠
    elif pct >= 70:
        return "#66cc66"  # 淺綠
    elif pct >= 30:
        return "#ffaa00"  # 橙色
    else:
        return "#ff4444"  # 紅色


# ==============================================
# 左側：New Project 表單
# ==============================================
with st.sidebar:
    st.header("New Project")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
            new_name = st.text_input("Project Name*")
            new_year = st.selectbox("Year*", [2024, 2025, 2026], index=1)
            new_qty = st.number_input("Qty", min_value=1, value=1)
        with col2:
            new_customer = st.text_input("Customer")
            new_supervisor = st.text_input("Supervisor")
            new_leadtime = st.date_input("Lead Time*", value=date.today())

        with st.expander("Project Specification & Progress Dates", expanded=False):
            st.markdown("**Specification**")
            spec_genset = st.text_input("Genset model")
            spec_alternator = st.text_input("Alternator Model")
            spec_controller = st.text_input("Controller")
            spec_breaker = st.text_input("Circuit breaker Size")
            spec_charger = st.text_input("Charger")

            st.markdown("**Progress Dates**")
            p1 = st.date_input("Parts Arrival", value=None, key="p1")
            p2 = st.date_input("Installation Complete", value=None, key="p2")
            p3 = st.date_input("Testing Complete", value=None, key="p3")
            p4 = st.date_input("Cleaning Complete", value=None, key="p4")
            p5 = st.date_input("Delivery Complete", value=None, key="p5")

            new_desc = st.text_area("Description", height=100)

        if st.form_submit_button("Add", type="primary", use_container_width=True):
            if not new_name.strip():
                st.error("Project Name is required!")
            elif new_name in df["Project_Name"].values:
                st.error("Project Name already exists!")
            else:
                spec_text = f"Genset model: {spec_genset or '—'}\nAlternator Model: {spec_alternator or '—'}\nController: {spec_controller or '—'}\nCircuit breaker Size: {spec_breaker or '—'}\nCharger: {spec_charger or '—'}"
                new_project = {
                    "Project_Type": new_type, "Project_Name": new_name, "Year": int(new_year),
                    "Lead_Time": new_leadtime.strftime("%Y-%m-%d"), "Customer": new_customer or "",
                    "Supervisor": new_supervisor or "", "Qty": new_qty, "Real_Count": new_qty,
                    "Project_Spec": spec_text, "Description": new_desc or "",
                    "Parts_Arrival": p1.strftime("%Y-%m-%d") if p1 else None,
                    "Installation_Complete": p2.strftime("%Y-%m-%d") if p2 else None,
                    "Testing_Complete": p3.strftime("%Y-%m-%d") if p3 else None,
                    "Cleaning_Complete": p4.strftime("%Y-%m-%d") if p4 else None,
                    "Delivery_Complete": p5.strftime("%Y-%m-%d") if p5 else None,
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                st.success(f"Added: {new_name}")
                st.rerun()

# ==============================================
# 中間：美觀彩色進度卡片
# ==============================================
st.title("YIP SHING Project List")

if len(df) == 0:
    st.info("No projects yet. Add one on the left!")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_progress_color(pct)

        with st.expander(f"**{row['Project_Name']}** • {row['Project_Type']} • {row.get('Customer', '—')}",
                         expanded=False):
            col_main, col_btn = st.columns([9, 2])

            with col_main:
                # 進度條
                st.markdown(f"""
                <div style="background: {color}; color: white; padding: 8px 15px; border-radius: 8px; font-weight: bold; margin-bottom: 10px;">
                    Progress: {pct}% 
                </div>
                <div style="background:#eee; border-radius:8px; overflow:hidden; height:10px; margin-bottom:15px;">
                    <div style="width:{pct}%; background:{color}; height:100%;"></div>
                </div>
                """, unsafe_allow_html=True)

                # 主要資訊
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:18px; border-radius:10px; border-left:6px solid {color};">
                    <p><strong>Year:</strong> {row['Year']} | <strong>Lead Time:</strong> {row['Lead_Time']}</p>
                    <p><strong>Customer:</strong> {row.get('Customer', '—')} | <strong>Supervisor:</strong> {row.get('Supervisor', '—')} | <strong>Qty:</strong> {row.get('Qty', 0)}</p>
                    {f"<pre style='background:#f0f0f0; padding:10px; border-radius:6px; margin:10px 0;'>{row.get('Project_Spec', '')}</pre>" if row.get('Project_Spec') else ""}
                    {f"<p><strong>Description:</strong><br>{row.get('Description', '—')}</p>" if row.get('Description') else ""}

                    <p style="margin-top:15px; color:#555;">
                        Parts Arrival: {row.get('Parts_Arrival', 'Not set')}<br>
                        Installation: {row.get('Installation_Complete', 'Not set')}<br>
                        Testing: {row.get('Testing_Complete', 'Not set')}<br>
                        Cleaning: {row.get('Cleaning_Complete', 'Not set')}<br>
                        Delivery: {row.get('Delivery_Complete', 'Not set')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                if st.button("Edit", key=f"edit_{idx}", use_container_width=True):
                    st.session_state[f"edit_{idx}"] = True
                if st.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    save_projects(df)
                    st.rerun()

            # Edit 功能（省略細節，與之前一樣，但包含 5 個日期欄位）
            # （如果你要我也可加上去，這裡先專注進度顯示）

st.markdown("---")
st.caption("Projects now have progress tracking • Color changes automatically • All data permanently saved")