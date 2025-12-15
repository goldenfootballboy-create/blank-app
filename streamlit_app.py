import streamlit as st
import pandas as pd
import os
import json
from datetime import date

# ==============================================
# 資料載入與儲存
# ==============================================
PROJECTS_FILE = "projects_data.json"
CHECKLIST_FILE = "checklist_data.json"


def init_files():
    if not os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(CHECKLIST_FILE):
        with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_projects() -> pd.DataFrame:
    init_files()
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    required = [
        "Project_Type", "Project_Name", "Year", "Lead_Time", "Customer", "Supervisor",
        "Qty", "Real_Count", "Project_Spec", "Description", "Progress_Reminder",
        "Parts_Arrival", "Installation_Complete", "Testing_Complete",
        "Cleaning_Complete", "Delivery_Complete"
    ]

    if not data:
        df = pd.DataFrame(columns=required)
    else:
        df = pd.DataFrame(data)

    for col in required:
        if col not in df.columns:
            df[col] = "" if col != "Year" else 2025

    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete",
                 "Testing_Complete", "Cleaning_Complete", "Delivery_Complete"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(date.today().year).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df["Qty"].fillna(1)

    return df


def save_projects(df: pd.DataFrame):
    df_save = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival", "Installation_Complete",
                 "Testing_Complete", "Cleaning_Complete", "Delivery_Complete"]
    for col in date_cols:
        if col in df_save.columns:
            df_save[col] = df_save[col].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None
            )
    df_save["Year"] = df_save["Year"].astype(int)
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df_save.to_dict("records"), f, ensure_ascii=False, indent=2)


def load_checklist() -> dict:
    init_files()
    with open(CHECKLIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checklist(data: dict):
    with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==============================================
# 計算與工具函數
# ==============================================
def calculate_progress(row):
    p = 0
    today = date.today()
    milestones = [
        ("Parts_Arrival", 30),
        ("Installation_Complete", 40),
        ("Testing_Complete", 10),
        ("Cleaning_Complete", 10),
        ("Delivery_Complete", 10),
    ]
    for col, weight in milestones:
        val = row.get(col)
        if pd.notna(val) and val.date() < today:
            p += weight
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
    return pd.to_datetime(d).strftime("%Y-%m-%d") if pd.notna(d) else "—"


# ==============================================
# 篩選邏輯
# ==============================================
def get_filtered_df(df: pd.DataFrame, view_mode: str, selected_type: str, selected_year: int, selected_month: str):
    all_df = df.copy()
    all_df["Lead_Time"] = pd.to_datetime(all_df["Lead_Time"], errors="coerce")

    if view_mode == "delay":
        # 安全處理：只有 Lead_Time 存在且已過期 + 進度未滿100
        if len(all_df) == 0 or "Lead_Time" not in all_df.columns:
            return pd.DataFrame()
        lead_passed = all_df["Lead_Time"].notna() & (all_df["Lead_Time"].dt.normalize() < pd.Timestamp(today()))
        progress_mask = all_df.apply(calculate_progress, axis=1) < 100
        return all_df[lead_passed & progress_mask].copy()

    else:
        filtered = all_df.copy()
        if selected_type != "All":
            filtered = filtered[filtered["Project_Type"] == selected_type]
        filtered = filtered[filtered["Year"] == selected_year]
        if selected_month != "All":
            month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                         "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
            month_num = month_map[selected_month]
            filtered = filtered[filtered["Lead_Time"].notna() &
                                (filtered["Lead_Time"].dt.month == month_num)]
        return filtered


# ==============================================
# UI 元件
# ==============================================
def sidebar_controls():
    with st.sidebar:
        st.header("View Controls")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("All Projects", use_container_width=True, type="primary"):
                st.session_state.view_mode = "all"
        with col2:
            if st.button("Delay Projects", use_container_width=True):
                st.session_state.view_mode = "delay"

        if "view_mode" not in st.session_state:
            st.session_state.view_mode = "all"

        project_types = ["All", "Enclosure", "Open Set", "Scania", "Marine", "K50G3"]
        years = [2024, 2025, 2026]
        months = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        if st.session_state.view_mode == "all":
            st.markdown("### Filters")
            type_sel = st.selectbox("Project Type", project_types, key="filter_type")
            year_sel = st.selectbox("Year", years, index=1, key="filter_year")
            month_sel = st.selectbox("Month", months, key="filter_month")
        else:
            type_sel = "All"
            year_sel = date.today().year
            month_sel = "All"

        st.markdown("---")
        st.header("New Project")
        # New project form (保持原樣，略縮減以節省篇幅)
        # ... (你可以直接貼回你原本的 New Project form 區塊)

        return st.session_state.view_mode, type_sel, year_sel, month_sel


def display_project_card(row, idx, checklist_db):
    pct = calculate_progress(row)
    color = get_color(pct)
    project_name = row["Project_Name"]

    # Checklist status
    check = checklist_db.get(project_name, {"purchase": [], "done_p": [], "drawing": [], "done_d": []})
    all_items = check["purchase"] + check["drawing"]
    done = set(check["done_p"]) | set(check["done_d"])
    real_items = [i for i in all_items if i and str(i).strip()]
    missing = any(str(i).strip() and str(i) not in done for i in real_items)
    empty = len(real_items) == 0
    all_done = len(real_items) > 0 and not missing

    status_tag = ""
    if empty:
        status_tag = '<span style="background:#888888;color:white;padding:4px 12px;border-radius:20px;font-size:0.8rem;margin-left:10px;">Please add checklist</span>'
    elif all_done:
        status_tag = '<span style="background:#00aa00;color:white;padding:4px 12px;border-radius:20px;font-size:0.8rem;margin-left:10px;">Check</span>'
    elif missing:
        status_tag = '<span style="background:#ff4444;color:white;padding:4px 12px;border-radius:20px;font-size:0.8rem;margin-left:10px;">Missing Submission</span>'

    reminder = str(row.get("Progress_Reminder", "")).strip() or "In Progress"
    reminder_html = f'<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-weight:bold;font-size:1.1rem;color:white;text-shadow:1px 1px 3px black;">{reminder}</div>'

    st.markdown(f"""
    <div style="background: linear-gradient(to right, {color} {pct}%, #f0f0f0 {pct}%); 
                border-radius:8px;padding:10px 15px;margin:10px 0;box-shadow:0 2px 6px rgba(0,0,0,0.1);position:relative;overflow:hidden;">
        {reminder_html}
        <div style="display:flex;justify-content:space-between;align-items:center;position:relative;z-index:5;">
            <div style="font-weight:bold;">{row['Project_Name']} • {row['Project_Type']}</div>
            <div>{status_tag}
                <span style="color:white;background:{color};padding:4px 12px;border-radius:20px;font-weight:bold;font-size:1rem;margin-left:10px;">{pct}%</span>
            </div>
        </div>
        <div style="font-size:0.85rem;color:#555;margin-top:6px;">
            {row.get('Customer', '—')} | {row.get('Supervisor', '—')} | Qty: {row.get('Qty', 0)} | Lead Time: {fmt(row['Lead_Time'])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Details • {project_name}", expanded=False):
        st.markdown(f"**Year:** {row['Year']} | **Lead Time:** {fmt(row['Lead_Time'])}")
        st.markdown(
            f"**Customer:** {row.get('Customer', '—')} | **Supervisor:** {row.get('Supervisor', '—')} | **Qty:** {row.get('Qty', 0)}")
        if row.get("Project_Spec"):
            st.markdown("**Project Specification:**")
            for line in row["Project_Spec"].split("\n"):
                if line.strip():
                    k, v = line.split(": ", 1) if ": " in line else ("", line)
                    st.markdown(f"• **{k}:** {v}")
        if row.get("Description"):
            st.markdown(f"**Description:** {row['Description']}")

        # Checklist / Edit / Delete 可以再進一步抽成子函數
        # 這裡保留原本邏輯（可自行貼回）


# ==============================================
# 主程式
# ==============================================
df = load_projects()
checklist_db = load_checklist()

view_mode, sel_type, sel_year, sel_month = sidebar_controls()

filtered_df = get_filtered_df(df, view_mode, sel_type, sel_year, sel_month)

title = "Delay Projects" if view_mode == "delay" else "YIP SHING Project Dashboard"
st.title(title)

if len(filtered_df) == 0:
    if view_mode == "delay":
        st.success("No delay projects! All on time!")
    else:
        st.info("No projects match the selected filters.")
else:
    # Counter
    total = int(filtered_df["Qty"].sum())
    by_type = filtered_df.groupby("Project_Type")["Qty"].sum().astype(int)
    counter_html = "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in by_type.items()])
    st.markdown(f"""
    <div style="position:fixed;top:70px;right:20px;background:#1e3a8a;color:white;padding:12px 18px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.3);z-index:1000;">
        <strong style="font-size:1.1rem;">Total: {total}</strong><br>{counter_html}
    </div>
    """, unsafe_allow_html=True)

    for idx, row in filtered_df.iterrows():
        display_project_card(row, idx, checklist_db)

st.markdown("---")
st.caption("Progress only counts when date has passed today • 永久儲存")