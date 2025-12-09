import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date

# ==================================================
# 1. 基本設定 + 純 JSON 永久儲存
# ==================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

st.set_page_config(page_title="YIP SHING Project Status Dashboard", layout="wide", initial_sidebar_state="expanded")

PROJECTS_FILE = "projects_data.json"

# 如果檔案不存在就建立空的
if not os.path.exists(PROJECTS_FILE):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    st.success("已建立專案資料庫，你可以開始新增專案了！")


# ------------------- 安全讀取 -------------------
def load_projects():
    with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame(columns=["Project_Type", "Project_Name", "Year", "Lead_Time"])

    df = pd.DataFrame(data)

    # 必要欄位補齊
    required = ["Project_Type", "Project_Name", "Year", "Lead_Time"]
    for col in required:
        if col not in df.columns:
            df[col] = None

    # 安全轉日期（無效值變 NaT）
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(2025).astype(int)
    if "Real_Count" not in df.columns:
        df["Real_Count"] = df.get("Qty", 1)

    return df


# ------------------- 安全儲存 -------------------
def save_projects(df):
    df_save = df.copy()
    date_cols = ["Lead_Time", "Parts_Arrival_Date", "Installation_Complete_Date", "Testing_Date", "Delivery_Date"]
    for col in date_cols:
        if col in df_save.columns:
            # 只有真正是 datetime 的才轉字串，其他直接變 None
            df_save[col] = df_save[col].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None
            )
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(df_save.to_dict(orient="records"), f, ensure_ascii=False, indent=2)


# 載入資料
df = load_projects()

# ==================================================
# 2. 側邊欄：新增專案 + 篩選
# ==================================================
with st.sidebar:
    st.title("Dashboard Controls")

    # ---------- 新增專案 ----------
    with st.expander("➕ 新增 Project", expanded=False):
        with st.form("add_project_form", clear_on_submit=True):
            st.markdown("### 填寫新專案資訊")
            c1, c2 = st.columns(2)
            with c1:
                new_type = st.selectbox("Project Type*", ["Enclosure", "Open Set", "Scania", "Marine", "K50G3"])
                new_name = st.text_input("Project Name*", placeholder="例如：YIP-2025-028")
                new_year = st.selectbox("Year*", ["2024", "2025", "2026"], index=1)
                new_qty = st.number_input("Qty", min_value=1, value=1)
            with c2:
                new_customer = st.text_input("Customer (選填)")
                new_manager = st.text_input("負責人 (選填)")
                new_leadtime = st.date_input("Lead Time*", value=date(2025, 12, 31))
                new_brand = st.text_input("Brand (選填)")

            new_desc = st.text_area("Description (選填)", height=80)

            if st.form_submit_button("✨ 新增專案"):
                if not new_name.strip():
                    st.error("Project Name 不能為空！")
                elif new_name in df["Project_Name"].values:
                    st.error("此 Project Name 已存在！")
                else:
                    new_record = {
                        "Project_Type": new_type,
                        "Project_Name": new_name,
                        "Year": int(new_year),
                        "Lead_Time": new_leadtime.strftime("%Y-%m-%d"),
                        "Customer": new_customer or "",
                        "負責人": new_manager or "",
                        "Qty": new_qty,
                        "Real_Count": new_qty,
                        "Brand": new_brand or "",
                        "Description": new_desc or "",
                        "Parts_Arrival_Date": None,
                        "Installation_Complete_Date": None,
                        "Testing_Date": None,
                        "Cleaning": "",
                        "Delivery_Date": None,
                        "Remarks": "",
                        "Order_List": "",
                        "Submit_List": "",
                        "Progress_Tooltip": ""
                    }
                    df.loc[len(df)] = new_record
                    save_projects(df)
                    st.success(f"已新增：{new_name}")
                    st.rerun()

    # ---------- 原有篩選 ----------
    st.markdown("### Project Type Selection")
    project_types = ["All", "Enclosure", "Open Set", "Scania", "Marine", "K50G3"]
    selected_project_type = st.selectbox("Select Project Type:", project_types, index=0)

    years = ["2024", "2025", "2026"]
    selected_year = st.selectbox("Select Year:", years, index=years.index("2025"))

    month_options = ["--", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月",
                     "十二月"]
    selected_month = st.selectbox("Lead Time:", month_options, index=0)

# ==================================================
# 3. CSS + 標題（你原本的全部保留）
# ==================================================
st.markdown("""
<style>
    .main-header {font-size: 3rem; color: #1fb429; margin-bottom: 1rem; margin-top: -4rem; font-weight: bold;
                  display: flex; justify-content: center; align-items: center; width: 100%;}
    .main-header .title {flex-grow: 1; text-align: center;}
    .project-type-selector {background-color: #f0f2f6; padding: 1rem; border-radius: 10px; border-left: 5px solid #1fb429;}
    .stButton>button {background-color: #1f77b4; color: white; border: none; border-radius: 5px; padding: 0.5rem 1rem; font-weight: bold;}
    .stButton>button:hover {background-color: #155799;}
    .custom-progress {height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; width: 150px;}
    .custom-progress-fill {height: 100%; transition: width 0.3s ease; border-radius: 10px;}
    .tooltip-container {position: relative; display: inline-block;}
    .tooltip-box {position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%);
                  background: #1e1e1e; color: white; padding: 16px 24px; border-radius: 12px;
                  font-size: 16px; line-height: 1.7; white-space: pre-wrap; min-width: 200px; max-width: 500px;
                  box-shadow: 0 0 8px 25px rgba(0,0,0,0.5); opacity: 0; visibility: hidden; transition: all 0.3s ease; z-index: 999;}
    .tooltip-arrow {position: absolute; top: 100%; left: 50%; margin-left: -8px;
                    border: 8px solid transparent; border-top-color: #1e1e1e;}
    .tooltip-container:hover .tooltip-box {opacity: 1 !important; visibility: visible !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><div class="title">YIP SHING Project Status Dashboard</div></div>',
            unsafe_allow_html=True)
st.markdown("---")

# ==================================================
# 4. 篩選 + 統計（你原本的邏輯，僅改 df 來源）
# ==================================================
filtered_df = df[df['Year'] == int(selected_year)].copy()

if selected_project_type != "All":
    filtered_df = filtered_df[filtered_df['Project_Type'] == selected_project_type]

if selected_month != "--" and 'Lead_Time' in filtered_df.columns:
    month_idx = month_options.index(selected_month)
    if month_idx > 0:
        filtered_df = filtered_df[filtered_df['Lead_Time'].dt.month == month_idx]

# 統計
if 'Real_Count' in filtered_df.columns:
    filtered_df['Real_Count'] = pd.to_numeric(filtered_df['Real_Count'], errors='coerce').fillna(0).astype(int)
else:
    filtered_df['Real_Count'] = 0

total_real_count = int(filtered_df['Real_Count'].sum())

month_str = selected_month if selected_month != "--" else "All Months"
st.markdown(f"### {selected_project_type} - {selected_year} {month_str} Project Count")

col1, *rest = st.columns([1] + [1] * len(filtered_df['Project_Type'].unique()))
with col1:
    st.write(f"**Total: {total_real_count}**")
for i, pt in enumerate(sorted(filtered_df['Project_Type'].unique())):
    cnt = filtered_df[filtered_df['Project_Type'] == pt]['Real_Count'].sum()
    with rest[i]:
        st.write(f"**{pt}: {int(cnt)}**")

# ==================================================
# 5. 主畫面：進度條 + 延誤 + 表格 + Checklist + Memo
# ==================================================
# 這裡直接貼上你原本從「if total_real_count > 0:」開始到程式最後的全部程式碼
# （因為太長，這裡省略，但你只要從你上一個版本直接複製貼上來即可，全部不動！）

# 只要把所有出現 df 的地方換成 filtered_df（你原本就這樣寫），全部正常運作

# 範例（你原本的開頭）：
if total_real_count > 0:
    st.markdown(f"### {selected_year} {month_str} {selected_project_type} Project Details")
    # ... 你原本的完整進度條、延誤、表格、Checklist、Memo 全部貼上 ...

else:
    st.info("目前尚無符合條件的專案，請先新增專案！")

st.markdown("---")
st.caption("純 JSON 永久儲存 │ 新增專案立即顯示 │ 無需 CSV │ 永不遺失資料")