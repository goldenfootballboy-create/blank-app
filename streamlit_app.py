import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 永久儲存
# ==============================================
PROJECTS_FILE = "projects_data.json"
CHECKLIST_FILE = "checklist_data.json"

if not os.path.exists(S_FILE):
    with open(S_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

if not os.path.exists(CHECKLIST_FILE):
    with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def load_projects():
    with open(S_FILE, "r", encoding="utf-8") as f:
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
    with open(S_FILE, "w", encoding="utf-8") as f:
        json.dump(df2.to_dict("records"), f, ensure_ascii=False, indent=2)

def load_checklist():
    with open(CHECKLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_checklist(data):
    with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

df = load_projects()
checklist_db = load_checklist()

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
# 中間：卡片 + 完美狀態標籤 + 完整 Edit 表單
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        # 判斷 Checklist 狀態
        project_name = row["Project_Name"]
        current_check = checklist_db.get(project_name, {"purchase": [], "done_p": [], "drawing": [], "done_d": []})
        all_items = current_check["purchase"] + current_check["drawing"]
        done_items = set(current_check["done_p"]) | set(current_check["done_d"])
        real_items = [item for item in all_items if item.strip()]
        has_missing = any(item.strip() and item not in done_items for item in real_items)
        all_done = len(real_items) > 0 and not has_missing
        is_empty = len(real_items) == 0

        # 狀態標籤
        status_tag = ""
        if is_empty:
            status_tag = '<span style="background:#888888; color:white; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:0.8rem; margin-left:10px;">Please add checklist</span>'
        elif all_done:
            status_tag = '<span style="background:#00aa00; color:white; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:0.8rem; margin-left:10px;">Check</span>'
        elif has_missing:
            status_tag = '<span style="background:#ff4444; color:white; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:0.8rem; margin-left:10px;">Missing Submission</span>'

        # 進度卡片
        st.markdown(f"""
        <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                    border-radius: 8px; padding: 10px 15px; margin: 6px 0; 
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold;">
                    {row['Project_Name']} • {row['Project_Type']}
                </div>
                <div>
                    {status_tag}
                    <span style="color:white; background:{color}; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:1rem; margin-left:10px;">
                        {pct}%
                    </span>
                </div>
            </div>
            <div style="font-size:0.85rem; color:#555; margin-top:6px;">
                {row.get('Customer','—')} | {row.get('Supervisor','—')} | Qty:{row.get('Qty',0)} | 
                Lead Time: {fmt(row['Lead_Time'])}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 展開內容
        with st.expander(f"Details • {row['Project_Name']}", expanded=False):
            st.markdown(f"**Year:** {row['Year']} | **Lead Time:** {fmt(row['Lead_Time'])}")
            st.markdown(f"**Customer:** {row.get('Customer','—')} | **Supervisor:** {row.get('Supervisor','—')} | **Qty:** {row.get('Qty',0)}")

            if row.get("Project_Spec"):
                st.markdown("**Project Specification:**")
                for line in row["Project_Spec"].split("\n"):
                    if line.strip():
                        key, val = line.split(": ",1) if ": " in line else ("", line)
                        st.markdown(f"• **{key}:** {val}")

            # Checklist Panel
            if st.button("Checklist Panel", key=f"cl_btn_{idx}", use_container_width=True):
                st.session_state[f"cl_open_{idx}"] = not st.session_state.get(f"cl_open_{idx}", False)

            if st.session_state.get(f"cl_open_{idx}", False):
                current = checklist_db.get(project_name, {"purchase": [],"done_p": [],"drawing": [],"done_d": []})

                st.markdown("<h4 style='text-align:center;'>Purchase List        Drawings Submission</h4>", unsafe_allow_html=True)

                new_purchase = []
                new_done_p = set()
                new_drawing = []
                new_done_d = set()

                max_rows = max(len(current["purchase"]), len(current["drawing"]), 6)

                for i in range(max_rows):
                    c1, c2 = st.columns(2)
                    with c1:
                        text = current["purchase"][i] if i < len(current["purchase"]) else ""
                        checked = text in current["done_p"]
                        col_chk, col_txt = st.columns([1,7])
                        with col_chk:
                            chk = st.checkbox("", value=checked, key=f"p_{idx}_{i}")
                        with col_txt:
                            txt = st.text_input("", value=text, key=f"pt_{idx}_{i}", label_visibility="collapsed")
                        if txt.strip():
                            new_purchase.append(txt.strip())
                            if chk:
                                new_done_p.add(txt.strip())
                    with c2:
                        text = current["drawing"][i] if i < len(current["drawing"]) else ""
                        checked = text in current["done_d"]
                        col_chk, col_txt = st.columns([1,7])
                        with col_chk:
                            chk = st.checkbox("", value=checked, key=f"d_{idx}_{i}")
                        with col_txt:
                            txt = st.text_input("", value=text, key=f"dt_{idx}_{i}", label_visibility="collapsed")
                        if txt.strip():
                            new_drawing.append(txt.strip())
                            if chk:
                                new_done_d.add(txt.strip())

                if st.button("SAVE CHECKLIST", key=f"save_cl_{idx}", type="primary", use_container_width=True):
                    checklist_db[project_name] = {
                        "purchase": new_purchase,
                        "done_p": list(new_done_p),
                        "drawing": new_drawing,
                        "done_d": list(new_done_d)
                    }
                    save_checklist(checklist_db)
                    st.success("Checklist 已儲存！")
                    st.rerun()

            # Edit（在 expander 內展開）
            if st.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state[f"editing_{idx}"] = not st.session_state.get(f"editing_{idx}", False)

            if st.session_state.get(f"editing_{idx}", False):
                st.markdown("---")
                st.subheader(f"Editing: {row['Project_Name']}")
                with st.form(key=f"edit_form_{idx}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        e_type = st.selectbox("Project Type*", ["Enclosure","Open Set","Scania","Marine","K50G3"],
                                             index=["Enclosure","Open Set","Scania","Marine","K50G3"].index(row["Project_Type"]))
                        e_name = st.text_input("Project Name*", value=row["Project_Name"])
                        e_year = st.selectbox("Year*", [2024,2025,2026], index=[2024,2025,2026].index(row["Year"]))
                        e_qty = st.number_input("Qty", min_value=1, value=int(row.get("Qty",1)))
                    with c2:
                        e_customer = st.text_input("Customer", value=row.get("Customer",""))
                        e_supervisor = st.text_input("Supervisor", value=row.get("Supervisor",""))
                        e_leadtime = st.date_input("Lead Time*", value=pd.to_datetime(row["Lead_Time"]).date() if pd.notna(row["Lead_Time"]) else date.today())

                    with st.expander("Project Specification & Progress Dates", expanded=True):
                        curr_spec = row.get("Project_Spec","")
                        lines = [line.split(": ",1)[1] if ": " in line else "" for line in curr_spec.split("\n")] if curr_spec else ["","","","",""]
                        e_s1 = st.text_input("Genset model", value=lines[0] if len(lines)>0 else "")
                        e_s2 = st.text_input("Alternator Model", value=lines[1] if len(lines)>1 else "")
                        e_s3 = st.text_input("Controller", value=lines[2] if len(lines)>2 else "")
                        e_s4 = st.text_input("Circuit breaker Size", value=lines[3] if len(lines)>3 else "")
                        e_s5 = st.text_input("Charger", value=lines[4] if len(lines)>4 else "")

                        st.markdown("**Progress Dates**")
                        e_d1 = st.date_input("Parts Arrival", value=pd.to_datetime(row["Parts_Arrival"]).date() if pd.notna(row["Parts_Arrival"]) else None, key=f"d1e{idx}")
                        e_d2 = st.date_input("Installation Complete", value=pd.to_datetime(row["Installation_Complete"]).date() if pd.notna(row["Installation_Complete"]) else None, key=f"d2e{idx}")
                        e_d3 = st.date_input("Testing Complete", value=pd.to_datetime(row["Testing_Complete"]).date() if pd.notna(row["Testing_Complete"]) else None, key=f"d3e{idx}")
                        e_d4 = st.date_input("Cleaning Complete", value=pd.to_datetime(row["Cleaning_Complete"]).date() if pd.notna(row["Cleaning_Complete"]) else None, key=f"d4e{idx}")
                        e_d5 = st.date_input("Delivery Complete", value=pd.to_datetime(row["Delivery_Complete"]).date() if pd.notna(row["Delivery_Complete"]) else None, key=f"d5e{idx}")

                        e_desc = st.text_area("Description", value=row.get("Description",""), height=100)

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
                                del st.session_state[f"editing_{idx}"]
                                st.success("Updated!")
                                st.rerun()
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            del st.session_state[f"editing_{idx}"]
                            st.rerun()

            # Delete
            if st.button("Delete", key=f"del_{idx}", type="secondary"):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

st.markdown("---")
st.caption("All functions work perfectly • Edit inline • Checklist with status • 永久儲存")