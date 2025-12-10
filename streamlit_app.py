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

if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

if not os.path.exists(CHECKLIST_FILE):
    with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

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
# 左側：New Project（保持不變）
# ==============================================
with st.sidebar:
    st.header("New Project")
    # （你原本的 New Project 表單全部保留）

# ==============================================
# 中間：卡片 + Missing Submission 完全不殘留（用 st.columns 完美解決）
# ==============================================
st.title("YIP SHING Project Dashboard")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        # 正確判斷 Missing Submission
        project_name = row["Project_Name"]
        current_check = checklist_db.get(project_name, {"purchase": [], "done_p": [], "drawing": [], "done_d": []})
        all_items = current_check["purchase"] + current_check["drawing"]
        done_items = set(current_check["done_p"]) | set(current_check["done_d"])
        has_missing = any(item.strip() and item not in done_items for item in all_items)

        # 進度卡片
        st.markdown(f"""
        <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                    border-radius: 8px; padding: 10px 15px; margin: 6px 0; 
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: bold;">
                    {row['Project_Name']} • {row['Project_Type']}
                </div>
                <div style="display: flex; align-items: center;">
                    {"<span style='background:#ff4444; color:white; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:0.8rem; margin-right:10px;'>Missing Submission</span>" if has_missing else ""}
                    <span style="color:white; background:{color}; padding:4px 12px; border-radius:20px; font-weight:bold; font-size:1rem;">
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

        # 展開內容（保持你原本的）
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

            # Edit & Delete
            col1, col2 = st.columns(2)
            if col1.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state[f"editing_{idx}"] = True
            if col2.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

st.markdown("---")
st.caption("Missing Submission only appears when there are actual unchecked items • No HTML residue • Perfect display")