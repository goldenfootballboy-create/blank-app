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

def fmt(d):
    return pd.to_datetime(d).strftime("%Y-%m-%d") if pd.notna(d) else "—"

# ==============================================
# 左側：New Project
# ==============================================
with st.sidebar:
    st.header("New Project")

    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_type = st.selectbox("Project Type*", ["Enclosure","Open Set","Scania","Marine","K50G3"])
            new_name = st.text_input("Project Name*")
            new_year = st.selectbox("Year*", [2024,2025,2026], index=1)
            new_qty  = st.number_input("Qty", min_value=1, value=1)
        with c2:
            new_customer = st.text_input("Customer")
            new_supervisor = st.text_input("Supervisor")
            new_leadtime = st.date_input("Lead Time*", value=date.today())

        with st.expander("Project Specification & Progress Dates", expanded=False):
            st.markdown("**Specification**")
            s1 = st.text_input("Genset model")
            s2 = st.text_input("Alternator Model")
            s3 = st.text_input("Controller")
            s4 = st.text_input("Circuit breaker Size")
            s5 = st.text_input("Charger")

            st.markdown("**Progress Dates**")
            d1 = st.date_input("Parts Arrival", value=None, key="d1")
            d2 = st.date_input("Installation Complete", value=None, key="d2")
            d3 = st.date_input("Testing Complete", value=None, key="d3")
            d4 = st.date_input("Cleaning Complete", value=None, key="d4")
            d5 = st.date_input("Delivery Complete", value=None, key="d5")

            desc = st.text_area("Description", height=100)

        if st.form_submit_button("Add", type="primary", use_container_width=True):
            if not new_name.strip():
                st.error("Project Name required!")
            elif new_name in df["Project_Name"].values:
                st.error("Name exists!")
            else:
                spec_lines = [
                    f"Genset model: {s1 or '—'}",
                    f"Alternator Model: {s2 or '—'}",
                    f"Controller: {s3 or '—'}",
                    f"Circuit breaker Size: {s4 or '—'}",
                    f"Charger: {s5 or '—'}"
                ]
                spec_text = "\n".join(spec_lines)

                new_project = {
                    "Project_Type": new_type, "Project_Name": new_name, "Year": int(new_year),
                    "Lead_Time": new_leadtime.strftime("%Y-%m-%d"), "Customer": new_customer or "",
                    "Supervisor": new_supervisor or "", "Qty": new_qty, "Real_Count": new_qty,
                    "Project_Spec": spec_text, "Description": desc or "",
                    "Parts_Arrival": d1.strftime("%Y-%m-%d") if d1 else None,
                    "Installation_Complete": d2.strftime("%Y-%m-%d") if d2 else None,
                    "Testing_Complete": d3.strftime("%Y-%m-%d") if d3 else None,
                    "Cleaning_Complete": d4.strftime("%Y-%m-%d") if d4 else None,
                    "Delivery_Complete": d5.strftime("%Y-%m-%d") if d5 else None,
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                st.success(f"Added: {new_name}")
                st.rerun()

# ==============================================
# 中間：Project Counter（只顯示數字） + 進度卡片
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) > 0:
    # 只顯示數字的超乾淨 Counter
    counter = df.groupby("Project_Type")["Qty"].sum().astype(int).sort_index()
    total_qty = int(df["Qty"].sum())

    cols = st.columns(len(counter) + 1)
    with cols[0]:
        st.markdown(f"<h2 style='text-align:center; margin:0; color:#1fb429;'>{total_qty}</h2>", unsafe_allow_html=True)
    for i, (ptype, qty) in enumerate(counter.items()):
        with cols[i+1]:
            st.markdown(f"<h2 style='text-align:center; margin:0;'>{qty}</h2>", unsafe_allow_html=True)
    st.markdown("---")

# 小巧進度卡片
if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
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
                {row.get('Customer','—')} | {row.get('Supervisor','—')} | Qty:{row.get('Qty',0)} | 
                Lead Time: {fmt(row['Lead_Time'])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Details • {row['Project_Name']}", expanded=False):
            st.markdown(f"**Year:** {row['Year']} | **Lead Time:** {fmt(row['Lead_Time'])}")
            st.markdown(f"**Customer:** {row.get('Customer','—')} | **Supervisor:** {row.get('Supervisor','—')} | **Qty:** {row.get('Qty',0)}")
            if row.get("Description"):
                st.markdown(f"**Description:** {row['Description']}")
            if row.get("Project_Spec"):
                st.markdown("**Project Specification:**")
                for line in row["Project_Spec"].split("\n"):
                    if line.strip():
                        key, val = line.split(": ",1) if ": " in line else ("", line)
                        st.markdown(f"• **{key}:** {val}")

            col1, col2 = st.columns(2)
            if col1.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.editing_index = idx
            if col2.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

st.markdown("---")
st.caption("YIP SHING • Qty counter • Clean progress cards • 永久儲存")