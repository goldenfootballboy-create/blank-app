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
    if "Lead_Time" in df.columns:
        df["Lead_Time"] = pd.to_datetime(df["Lead_Time"], errors="coerce")
    if "Year" not in df.columns:
        df["Year"] = 2025
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)
    if "Project_Spec" not in df.columns:
        df["Project_Spec"] = ""
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
# 左側：New Project 表單（Project Spec. 按鈕移出 form）
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
            new_supervisor = st.text_input("Supervisor")
            new_leadtime = st.date_input("Lead Time*", value=date.today())

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
                    "Supervisor": new_supervisor or "",
                    "Qty": new_qty,
                    "Real_Count": new_qty,
                    "Project_Spec": st.session_state.get("temp_project_spec", ""),
                    "Description": new_desc or "",
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                # 清空暫存
                if "temp_project_spec" in st.session_state:
                    del st.session_state.temp_project_spec
                if "show_spec_form" in st.session_state:
                    del st.session_state.show_spec_form
                st.success(f"Added: {new_name}")
                st.rerun()

    # Project Spec. 按鈕放在 form 外面
    if st.button("Project Spec.", type="secondary", use_container_width=True):
        st.session_state.show_spec_form = True

    # 彈出 Project Spec. 輸入方格
    if st.session_state.get("show_spec_form", False):
        with st.expander("Project Specification", expanded=True):
            spec_genset = st.text_input("Genset model", value=st.session_state.get("spec_genset", ""))
            spec_alternator = st.text_input("Alternator Model", value=st.session_state.get("spec_alternator", ""))
            spec_controller = st.text_input("Controller", value=st.session_state.get("spec_controller", ""))
            spec_breaker = st.text_input("Circuit breaker Size", value=st.session_state.get("spec_breaker", ""))
            spec_charger = st.text_input("Charger", value=st.session_state.get("spec_charger", ""))

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Spec", type="primary"):
                    spec_text = f"Genset model: {spec_genset}\nAlternator Model: {spec_alternator}\nController: {spec_controller}\nCircuit breaker Size: {spec_breaker}\nCharger: {spec_charger}"
                    st.session_state.temp_project_spec = spec_text
                    st.session_state.show_spec_form = False
                    st.success("Project Spec saved! Now click Add to create project.")
                    st.rerun()
            with col_cancel:
                if st.button("Cancel"):
                    st.session_state.show_spec_form = False
                    st.rerun()

# ==============================================
# 中間：專案列表 + Edit + Delete + Project Spec 顯示
# ==============================================
st.title("YIP SHING Project List")

if len(df) == 0:
    st.info("No projects yet. Please add your first project on the left.")
else:
    total = df["Real_Count"].sum() if "Real_Count" in df.columns else len(df)
    st.markdown(f"**Total Projects: {int(total)}**")
    st.markdown("---")

    for idx, row in df.iterrows():
        with st.expander(
                f"**{row['Project_Name']}** • {row['Project_Type']} • {row.get('Customer', '') or 'No Customer'}",
                expanded=False):
            col_content, col_buttons = st.columns([8, 2])

            with col_content:
                st.markdown(f"""
                <div style="background:#f9f9f9; padding:20px; border-radius:10px; border-left:6px solid #1fb429;">
                    <p style="margin:5px 0; font-size:1.1rem;">
                        <strong>Year:</strong> {row['Year']} &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Lead Time:</strong> {pd.to_datetime(row['Lead_Time']).strftime('%Y-%m-%d') if pd.notna(row['Lead_Time']) else 'Not set'}
                    </p>
                    <p style="margin:5px 0; font-size:1.1rem;">
                        <strong>Customer:</strong> {row.get('Customer', '—')} &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Supervisor:</strong> {row.get('Supervisor', '—')} &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Qty:</strong> {row.get('Qty', 0)}
                    </p>
                    {f"<p style='margin:10px 0; font-size:1.1rem; line-height:1.6; white-space: pre-wrap;'><strong>Project Spec.:</strong><br>{row.get('Project_Spec', '—')}</p>" if row.get('Project_Spec') else ""}
                    {f"<p style='margin:10px 0; font-size:1.1rem; line-height:1.5;'><strong>Description:</strong><br>{row.get('Description', '—')}</p>" if row.get('Description') else ""}
                </div>
                """, unsafe_allow_html=True)

            with col_buttons:
                if st.button("Edit", key=f"edit_{idx}", type="secondary", use_container_width=True):
                    st.session_state[f"editing_{idx}"] = True

                if st.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    save_projects(df)
                    st.success(f"Deleted: {row['Project_Name']}")
                    st.rerun()

            # 編輯模式（簡化版，Project Spec. 編輯稍後再加，如果你需要現在告訴我）
            if st.session_state.get(f"editing_{idx}", False):
                st.markdown("---")
                st.write("Edit function coming soon... (or cancel)")
                if st.button("Cancel Edit", key=f"cancel_{idx}"):
                    st.session_state[f"editing_{idx}"] = False
                    st.rerun()

st.markdown("---")
st.caption(
    "Project Spec. button is now outside the form • Click to enter specification • Add project after saving spec")