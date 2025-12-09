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
    required = ["Project_Type", "Project_Name", "Year", "Lead_Time", "Customer", "Supervisor",
                "Qty", "Real_Count", "Project_Spec", "Description",
                "Parts_Arrival", "Installation_Complete", "Testing_Complete", "Cleaning_Complete", "Delivery_Complete"]
    for col in required:
        if col not in df.columns:
            df[col] = None

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


def fmt(d):
    return pd.to_datetime(d).strftime("%Y-%m-%d") if pd.notna(d) else "Not set"


# ==============================================
# 左側：New Project
# ==============================================
with st.sidebar:
    st.header("New Project")

    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
            new_name = st.text_input("Project Name*")
            new_year = st.selectbox("Year*", [2024, 2025, 2026], index=1)
            new_qty = st.number_input("Qty", min_value=1, value=1)
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
# 中間：專案列表（Project Spec. 在下面一行一行）
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        with st.expander(f"**{row['Project_Name']}** • {row['Project_Type']} • {row.get('Customer', '—')}",
                         expanded=False):
            col_l, col_r = st.columns([9, 2])

            with col_l:
                st.markdown(f"""
                <div style="background:{color}; color:white; padding:10px 20px; border-radius:8px; font-weight:bold;">
                    Progress: {pct}% Complete
                </div>
                <div style="background:#eee; border-radius:8px; overflow:hidden; height:12px; margin:10px 0;">
                    <div style="width:{pct}%; background:{color}; height:100%;"></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background:#f8f9fa; padding:20px; border-radius:10px; border-left:8px solid {color}; line-height:1.8;">
                    <p><strong>Year:</strong> {row['Year']} | <strong>Lead Time:</strong> {fmt(row['Lead_Time'])}</p>
                    <p><strong>Customer:</strong> {row.get('Customer', '—')} | <strong>Supervisor:</strong> {row.get('Supervisor', '—')} | <strong>Qty:</strong> {row.get('Qty', 0)}</p>
                    {f"<p><strong>Description:</strong><br>{row.get('Description', '—')}</p>" if row.get('Description') else ""}
                </div>
                """, unsafe_allow_html=True)

                # Project Spec. 在下面一行一行
                if row.get("Project_Spec"):
                    st.markdown("**Project Specification:**")
                    for line in row["Project_Spec"].split("\n"):
                        if line.strip():
                            key, value = line.split(": ", 1) if ": " in line else ("", line)
                            st.markdown(f"• <strong>{key}:</strong> {value}", unsafe_allow_html=True)

            with col_r:
                if st.button("Edit", key=f"edit_{idx}", use_container_width=True):
                    st.session_state.editing_index = idx

                if st.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                    df = df.drop(idx).reset_index(drop=True)
                    save_projects(df)
                    st.rerun()

            # ============ 完整 Edit 表單 ============
            if st.session_state.get("editing_index") == idx:
                st.markdown("---")
                st.subheader(f"Editing: {row['Project_Name']}")
                with st.form(key=f"edit_form_{idx}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        e_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"],
                                              index=["Enclosure", "Open Set", "Scania", "Marine", "K50G3"].index(
                                                  row["Project_Type"]) if row["Project_Type"] in ["Enclosure",
                                                                                                  "Open Set", "Scania",
                                                                                                  "Marine",
                                                                                                  "K50G3"] else 0)
                        e_name = st.text_input("Project Name*", value=row["Project_Name"])
                        e_year = st.selectbox("Year*", [2024, 2025, 2026],
                                              index=[2024, 2025, 2026].index(row["Year"]) if row["Year"] in [2024, 2025,
                                                                                                             2026] else 1)
                        e_qty = st.number_input("Qty", min_value=1, value=int(row.get("Qty", 1)))
                    with c2:
                        e_customer = st.text_input("Customer", value=row.get("Customer", ""))
                        e_supervisor = st.text_input("Supervisor", value=row.get("Supervisor", ""))
                        e_leadtime = st.date_input("Lead Time*",
                                                   value=pd.to_datetime(row["Lead_Time"]).date() if pd.notna(
                                                       row["Lead_Time"]) else date.today())

                    with st.expander("Project Specification & Progress Dates", expanded=True):
                        curr_spec = row.get("Project_Spec", "")
                        lines = [line.split(": ", 1)[1] if ": " in line else "" for line in
                                 curr_spec.split("\n")] if curr_spec else ["", "", "", "", ""]
                        e_s1 = st.text_input("Genset model", value=lines[0] if len(lines) > 0 else "")
                        e_s2 = st.text_input("Alternator Model", value=lines[1] if len(lines) > 1 else "")
                        e_s3 = st.text_input("Controller", value=lines[2] if len(lines) > 2 else "")
                        e_s4 = st.text_input("Circuit breaker Size", value=lines[3] if len(lines) > 3 else "")
                        e_s5 = st.text_input("Charger", value=lines[4] if len(lines) > 4 else "")

                        st.markdown("**Progress Dates**")
                        e_d1 = st.date_input("Parts Arrival",
                                             value=pd.to_datetime(row["Parts_Arrival"]).date() if pd.notna(
                                                 row["Parts_Arrival"]) else None, key=f"d1e{idx}")
                        e_d2 = st.date_input("Installation Complete",
                                             value=pd.to_datetime(row["Installation_Complete"]).date() if pd.notna(
                                                 row["Installation_Complete"]) else None, key=f"d2e{idx}")
                        e_d3 = st.date_input("Testing Complete",
                                             value=pd.to_datetime(row["Testing_Complete"]).date() if pd.notna(
                                                 row["Testing_Complete"]) else None, key=f"d3e{idx}")
                        e_d4 = st.date_input("Cleaning Complete",
                                             value=pd.to_datetime(row["Cleaning_Complete"]).date() if pd.notna(
                                                 row["Cleaning_Complete"]) else None, key=f"d4e{idx}")
                        e_d5 = st.date_input("Delivery Complete",
                                             value=pd.to_datetime(row["Delivery_Complete"]).date() if pd.notna(
                                                 row["Delivery_Complete"]) else None, key=f"d5e{idx}")

                        e_desc = st.text_area("Description", value=row.get("Description", ""), height=100)

                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("Save Changes", type="primary"):
                            if not e_name.strip():
                                st.error("Project Name required!")
                            else:
                                new_spec = "\n".join([
                                    f"Genset model: {e_s1 or '—'}",
                                    f"Alternator Model: {e_s2 or '—'}",
                                    f"Controller: {e_s3 or '—'}",
                                    f"Circuit breaker Size: {e_s4 or '—'}",
                                    f"Charger: {e_s5 or '—'}"
                                ])
                                df.at[idx, "Project_Type"] = e_type
                                df.at[idx, "Project_Name"] = e_name
                                df.at[idx, "Year"] = int(e_year)
                                df.at[idx, "Lead_Time"] = e_leadtime.strftime("%Y-%m-%d")
                                df.at[idx, "Customer"] = e_customer or ""
                                df.at[idx, "Supervisor"] = e_supervisor or ""
                                df.at[idx, "Qty"] = e_qty
                                df.at[idx, "Real_Count"] = e_qty
                                df.at[idx, "Project_Spec"] = new_spec
                                df.at[idx, "Description"] = e_desc or ""
                                df.at[idx, "Parts_Arrival"] = e_d1.strftime("%Y-%m-%d") if e_d1 else None
                                df.at[idx, "Installation_Complete"] = e_d2.strftime("%Y-%m-%d") if e_d2 else None
                                df.at[idx, "Testing_Complete"] = e_d3.strftime("%Y-%m-%d") if e_d3 else None
                                df.at[idx, "Cleaning_Complete"] = e_d4.strftime("%Y-%m-%d") if e_d4 else None
                                df.at[idx, "Delivery_Complete"] = e_d5.strftime("%Y-%m-%d") if e_d5 else None
                                save_projects(df)
                                del st.session_state.editing_index
                                st.success("Updated!")
                                st.rerun()
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            del st.session_state.editing_index
                            st.rerun()

st.markdown("---")
st.caption("All projects permanently saved • Edit function fully working • Progress auto-updates")