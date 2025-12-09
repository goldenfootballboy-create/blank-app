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
# 左側：New Project 表單（Brand 改為 Project Spec. 按鈕）
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

        # Project Spec. 按鈕 + 彈出輸入框
        if st.button("Project Spec.", type="secondary", use_container_width=True):
            st.session_state.show_spec = True

        if st.session_state.get("show_spec", False):
            with st.expander("Project Specification", expanded=True):
                spec_genset = st.text_input("Genset model", value=st.session_state.get("spec_genset", ""))
                spec_alternator = st.text_input("Alternator Model", value=st.session_state.get("spec_alternator", ""))
                spec_controller = st.text_input("Controller", value=st.session_state.get("spec_controller", ""))
                spec_breaker = st.text_input("Circuit breaker Size", value=st.session_state.get("spec_breaker", ""))
                spec_charger = st.text_input("Charger", value=st.session_state.get("spec_charger", ""))

                if st.button("Save Spec", key="save_spec"):
                    spec_text = f"Genset model: {spec_genset}\nAlternator Model: {spec_alternator}\nController: {spec_controller}\nCircuit breaker Size: {spec_breaker}\nCharger: {spec_charger}"
                    st.session_state.project_spec = spec_text
                    st.session_state.show_spec = False
                    st.success("Project Spec saved!")
                    st.rerun()

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
                    "Project_Spec": st.session_state.get("project_spec", ""),
                    "Description": new_desc or "",
                }
                df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
                save_projects(df)
                # 清空 spec 暫存
                for key in ["project_spec", "show_spec", "spec_genset", "spec_alternator", "spec_controller",
                            "spec_breaker", "spec_charger"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success(f"Added: {new_name}")
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

            # 編輯模式（也支援修改 Project Spec.）
            if st.session_state.get(f"editing_{idx}", False):
                st.markdown("---")
                with st.form(key=f"edit_form_{idx}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_type = st.selectbox("Project Type*",
                                                 ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"],
                                                 index=["Enclosure", "Open Set", "Scania", "Marine", "K50G3"].index(
                                                     row["Project_Type"]) if row["Project_Type"] in ["Enclosure",
                                                                                                     "Open Set",
                                                                                                     "Scania", "Marine",
                                                                                                     "K50G3"] else 0,
                                                 key=f"type_e{idx}")
                        edit_name = st.text_input("Project Name*", value=row["Project_Name"], key=f"name_e{idx}")
                        edit_year = st.selectbox("Year*", [2024, 2025, 2026],
                                                 index=[2024, 2025, 2026].index(row["Year"]) if row["Year"] in [2024,
                                                                                                                2025,
                                                                                                                2026] else 1,
                                                 key=f"year_e{idx}")
                        edit_qty = st.number_input("Qty", min_value=1, value=int(row.get("Qty", 1)), key=f"qty_e{idx}")
                    with col2:
                        edit_customer = st.text_input("Customer", value=row.get("Customer", ""), key=f"cust_e{idx}")
                        edit_supervisor = st.text_input("Supervisor", value=row.get("Supervisor", ""),
                                                        key=f"sup_e{idx}")
                        edit_leadtime = st.date_input("Lead Time*",
                                                      value=pd.to_datetime(row["Lead_Time"]).date() if pd.notna(
                                                          row["Lead_Time"]) else date.today(), key=f"lead_e{idx}")

                    # Project Spec. 編輯按鈕
                    current_spec = row.get("Project_Spec", "")
                    if st.button("Edit Project Spec.", key=f"spec_btn_{idx}", type="secondary",
                                 use_container_width=True):
                        st.session_state[f"edit_spec_{idx}"] = True

                    if st.session_state.get(f"edit_spec_{idx}", False):
                        with st.expander("Edit Project Specification", expanded=True):
                            spec_lines = current_spec.split("\n") if current_spec else ["", "", "", "", ""]
                            spec_genset = st.text_input("Genset model",
                                                        value=spec_lines[0].replace("Genset model: ", "") if len(
                                                            spec_lines) > 0 else "", key=f"gs_{idx}")
                            spec_alternator = st.text_input("Alternator Model",
                                                            value=spec_lines[1].replace("Alternator Model: ",
                                                                                        "") if len(
                                                                spec_lines) > 1 else "", key=f"alt_{idx}")
                            spec_controller = st.text_input("Controller",
                                                            value=spec_lines[2].replace("Controller: ", "") if len(
                                                                spec_lines) > 2 else "", key=f"con_{idx}")
                            spec_breaker = st.text_input("Circuit breaker Size",
                                                         value=spec_lines[3].replace("Circuit breaker Size: ",
                                                                                     "") if len(spec_lines) > 3 else "",
                                                         key=f"brk_{idx}")
                            spec_charger = st.text_input("Charger", value=spec_lines[4].replace("Charger: ", "") if len(
                                spec_lines) > 4 else "", key=f"chg_{idx}")

                            if st.button("Save Spec", key=f"save_spec_e{idx}"):
                                new_spec = f"Genset model: {spec_genset}\nAlternator Model: {spec_alternator}\nController: {spec_controller}\nCircuit breaker Size: {spec_breaker}\nCharger: {spec_charger}"
                                st.session_state[f"temp_spec_{idx}"] = new_spec
                                st.session_state[f"edit_spec_{idx}"] = False
                                st.success("Spec updated!")
                                st.rerun()

                    edit_desc = st.text_area("Description", value=row.get("Description", ""), height=100,
                                             key=f"desc_e{idx}")

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        save_edit = st.form_submit_button("Save Changes", type="primary")
                    with col_cancel:
                        cancel_edit = st.form_submit_button("Cancel")

                    if save_edit:
                        if not edit_name.strip():
                            st.error("Project Name is required!")
                        else:
                            df.at[idx, "Project_Type"] = edit_type
                            df.at[idx, "Project_Name"] = edit_name
                            df.at[idx, "Year"] = int(edit_year)
                            df.at[idx, "Lead_Time"] = edit_leadtime.strftime("%Y-%m-%d")
                            df.at[idx, "Customer"] = edit_customer or ""
                            df.at[idx, "Supervisor"] = edit_supervisor or ""
                            df.at[idx, "Qty"] = edit_qty
                            df.at[idx, "Real_Count"] = edit_qty
                            df.at[idx, "Project_Spec"] = st.session_state.get(f"temp_spec_{idx}", current_spec)
                            df.at[idx, "Description"] = edit_desc or ""
                            save_projects(df)
                            for key in [f"editing_{idx}", f"edit_spec_{idx}", f"temp_spec_{idx}"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.success(f"Updated: {edit_name}")
                            st.rerun()

                    if cancel_edit:
                        for key in [f"editing_{idx}", f"edit_spec_{idx}", f"temp_spec_{idx}"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

st.markdown("---")
st.caption("Project Spec. button opens specification fields • All data permanently saved")