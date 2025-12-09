import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 永久儲存 JSON（超級穩定）
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


df = load_projects()

# ==============================================
# 左側：New Project 表單
# ==============================================
with st.sidebar:
    st.header("New Project")

    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
            new_name = st.text_input("Project Name*", placeholder="e.g. YIP-2025-001")
            new_year = st.selectbox("Year*", [2024, 2025, 2026], index=1)
            new_qty = st.number_input("Qty", min_value=1, value=1)
        with col2:
            new_customer = st.text_input("Customer")
            new_manager = st.text_input("Manager")
            new_leadtime = st.date_input("Lead Time*", value=date.today())
            new_brand = st.text_input("Brand")

        new_desc = st.text_area("Description", height=100)

        if st.form_submit_button("Add", type="primary", use_container_width=True):
            if not new_name.strip():
                st.error("Project Name is required!")
            elif new_name in df["Project_Name"].values if len(df) > 0 else False:
                st.error("Project Name already exists!")
            else:
                new_project = {
                    "Project_Type": new_type,
                    "Project_Name": new_name,
                    "Year": int(new_year),
                    "Lead_Time": new_leadtime.strftime("%Y-%m-%d"),
                    "Customer": new_customer or "",
                    "Manager": new_manager or "",
                    "Qty": new_qty,
                    "Real_Count": new_qty,
                    "Brand": new_brand or "",
                    "Description": new_desc or "",
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                st.success(f"Added: {new_name}")
                st.rerun()

# ==============================================
# 中間：大卡片顯示所有專案 + 刪除功能
# ==============================================
st.title("YIP SHING Project List")

if len(df) == 0:
    st.info("No projects yet. Please add your first project on the left.")
else:
    total = df["Real_Count"].sum() if "Real_Count" in df.columns else len(df)
    st.markdown(f"**Total Projects: {int(total)}**")
    st.markdown("---")

    # 逐筆顯示大卡片
    for idx, row in df.iterrows():
        with st.container():
            col_main, col_del = st.columns([10, 1])

            with col_main:
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:20px; border-radius:12px; border-left:6px solid #1fb429; margin-bottom:15px;">
                    <h3 style="margin:0; color:#1fb429;">{row['Project_Name']}</h3>
                    <p style="margin:5px 0; color:#555;">
                        <strong>Type:</strong> {row['Project_Type']} &nbsp;|&nbsp; 
                        <strong>Year:</strong> {row['Year']} &nbsp;|&nbsp; 
                        <strong>Lead Time:</strong> {pd.to_datetime(row['Lead_Time']).strftime('%Y-%m-%d') if pd.notna(row['Lead_Time']) else 'Not set'}
                    </p>
                    <p style="margin:5px 0;">
                        <strong>Customer:</strong> {row.get('Customer', '—')} &nbsp;|&nbsp; 
                        <strong>Manager:</strong> {row.get('Manager', '—')} &nbsp;|&nbsp; 
                        <strong>Qty:</strong> {row.get('Qty', 0)}
                    </p>
                    <p style="margin:5px 0;"><strong>Brand:</strong> {row.get('Brand', '—')}</p>
                    {f"<p style='margin:10px 0; font-style:italic; color:#666;'><strong>Description:</strong><br>{row.get('Description', '—')}</p>" if row.get('Description') else ""}
                </div>
                """, unsafe_allow_html=True)

            with col_del:
                if st.button("Delete", key=f"del_{idx}", type="secondary"):
                    df = df.drop(idx).reset_index(drop=True)
                    save_projects(df)
                    st.success(f"Deleted: {row['Project_Name']}")
                    st.rerun()

st.caption("All projects are permanently saved • Add and delete instantly reflected after adding/deleting")