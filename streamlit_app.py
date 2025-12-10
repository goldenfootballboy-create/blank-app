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
# 進度計算 + 顏色 + 日期格式化
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
# 左側：New Project（保持你原本的）
# ==============================================
with st.sidebar:
    st.header("New Project")
    # 你原本的完整 New Project 表單貼在這裡（不變）

# ==============================================
# 中間：小巧卡片 + Checklist Panel
# ==============================================
st.title("YIP SHING Project Dashboard")

# 小巧 Counter
if len(df) > 0:
    counter = df.groupby("Project_Type")["Qty"].sum().astype(int).sort_index()
    total_qty = int(df["Qty"].sum())
    counter_html = f"<div style='text-align:center; margin:10px 0; font-size:0.95rem;'>"
    counter_html += f"<strong style='color:#1fb429; margin-right:20px;'>Total: {total_qty}</strong>"
    for ptype, qty in counter.items():
        counter_html += f"<strong style='margin-right:18px;'>{ptype}: {qty}</strong>  "
    counter_html += "</div>"
    st.markdown(counter_html, unsafe_allow_html=True)
    st.markdown("---")

if len(df) == 0:
    st.info("No projects yet. Add one on the left.")
else:
    for idx, row in df.iterrows():
        pct = calculate_progress(row)
        color = get_color(pct)

        # 小巧進度卡片
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

        # Details + Checklist Panel
        with st.expander(f"Details • {row['Project_Name']}", expanded=False):
            st.markdown(f"**Year:** {row['Year']} | **Lead Time:** {fmt(row['Lead_Time'])}")
            st.markdown(f"**Customer:** {row.get('Customer','—')} | **Supervisor:** {row.get('Supervisor','—')} | **Qty:** {row.get('Qty',0)}")

            # Project Spec
            if row.get("Project_Spec"):
                st.markdown("**Project Specification:**")
                for line in row["Project_Spec"].split("\n"):
                    if line.strip():
                        key, val = line.split(": ",1) if ": " in line else ("", line)
                        st.markdown(f"• **{key}:** {val}")

            # Checklist Panel
            if st.button("Checklist Panel", key=f"check_{idx}", use_container_width=True):
                st.session_state[f"show_checklist_{idx}"] = True

            if st.session_state.get(f"show_checklist_{idx}", False):
                project_name = row["Project_Name"]
                items = checklist_db.get(project_name, [])

                st.markdown("#### Checklist")
                new_items = []
                for i, item in enumerate(items):
                    col1, col2 = st.columns([6,1])
                    with col1:
                        text = st.text_input("", value=item.get("text",""), key=f"text_{idx}_{i}", label_visibility="collapsed")
                    with col2:
                        done = st.checkbox("", value=item.get("done",False), key=f"done_{idx}_{i}")
                    if text.strip():
                        new_items.append({"text": text.strip(), "done": done})

                # 新增項目
                new_text = st.text_input("Add new item", key=f"newitem_{idx}")
                if st.button("Add Item", key=f"additem_{idx}"):
                    if new_text.strip():
                        new_items.append({"text": new_text.strip(), "done": False})

                # 儲存
                if st.button("Save Checklist", key=f"savecheck_{idx}", type="primary"):
                    checklist_db[project_name] = new_items
                    save_checklist(checklist_db)
                    st.success("Checklist saved!")
                    st.rerun()

                # 顯示未完成項目（紅色提醒）
                pending = [it["text"] for it in new_items if it["text"] and not it["done"]]
                if pending:
                    st.markdown("**Pending items ❗**")
                    for p in pending:
                        st.markdown(f"• <span style='color:red; font-weight:bold;'>{p} 未完成</span>", unsafe_allow_html=True)
                else:
                    st.success("All items completed!")

            # Edit & Delete
            col1, col2 = st.columns(2)
            if col1.button("Edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.editing_index = idx
            if col2.button("Delete", key=f"del_{idx}", type="secondary", use_container_width=True):
                df = df.drop(idx).reset_index(drop=True)
                save_projects(df)
                st.rerun()

st.markdown("---")
st.caption("Checklist Panel added • Unfinished items shown in red • All data permanently saved")