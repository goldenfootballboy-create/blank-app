import streamlit as st
import pandas as pd
import requests
import json
from datetime import date, timedelta

# === 從 Secrets 讀取 ===
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GIST_ID = st.secrets["GIST_ID"]
API_URL = f"https://api.github.com/gists/{GIST_ID}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# === 讀取資料（縮短快取時間 + 可手動清除）===
@st.cache_data(ttl=30, show_spinner="正在從雲端載入資料...")
def load_data():
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        gist = response.json()
        files = gist.get("files", {})

        if not files:
            return pd.DataFrame(columns=["Project ID", "Customer", "負責人", "預計交付日期"])

        filename = next(iter(files))
        content = files[filename].get("content", "[]")
        data = json.loads(content)

        if not data:
            return pd.DataFrame(columns=["Project ID", "Customer", "負責人", "預計交付日期"])

        df = pd.DataFrame(data)

        required = ["Project ID", "Customer", "負責人", "預計交付日期"]
        for col in required:
            if col not in df.columns:
                df[col] = None

        if "預計交付日期" in df.columns:
            df["預計交付日期"] = pd.to_datetime(df["預計交付日期"], errors='coerce').dt.date

        return df[required]

    except Exception as e:
        st.error(f"載入資料失敗：{e}")
        return pd.DataFrame(columns=["Project ID", "Customer", "負責人", "預計交付日期"])


# === 儲存資料並強制清除快取 ===
def save_data(df):
    try:
        df_save = df.copy()
        if "預計交付日期" in df_save.columns:
            df_save["預計交付日期"] = df_save["預計交付日期"].astype(str)

        content = json.dumps(df_save.to_dict(orient="records"), indent=2, ensure_ascii=False)

        payload = {
            "description": "YIP SHING Project Database - Updated",
            "files": {
                "projects.json": {
                    "content": content
                }
            }
        }
        response = requests.patch(API_URL, headers=headers, json=payload)
        response.raise_for_status()

        # 關鍵：清除快取，讓下次 load_data 讀最新資料
        load_data.clear()

    except Exception as e:
        st.error(f"儲存失敗：{e}")


# === 主程式 ===
st.set_page_config(page_title="YIP SHING Project Database", layout="wide")
st.title("🗂️ YIP SHING Project Database")

df = load_data()

# === 新增 Project（立即儲存 + 清除快取 + 刷新）===
st.sidebar.header("📝 新增 Project")
with st.sidebar.form("add_form", clear_on_submit=True):
    st.markdown("### 填寫以下資訊新增專案")

    new_id = st.text_input("Project ID*", placeholder="例如: YIP-004")
    new_customer = st.text_input("Customer*", placeholder="客戶名稱")
    new_manager = st.text_input("負責人*", placeholder="負責人姓名")
    new_date = st.date_input(
        "預計交付日期 (Lead Time)*",
        value=date.today() + timedelta(days=60),
        min_value=date.today()
    )

    submitted = st.form_submit_button("✨ 新增 Project")

    if submitted:
        if not (new_id and new_customer and new_manager):
            st.error("請填寫所有必填欄位（*）")
        elif new_id in df["Project ID"].values:
            st.error("此 Project ID 已存在！")
        else:
            new_row = pd.DataFrame([{
                "Project ID": new_id,
                "Customer": new_customer,
                "負責人": new_manager,
                "預計交付日期": new_date
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)  # 儲存並清除快取
            st.success(f"✅ 已新增 Project: {new_id}，畫面即將更新...")
            st.rerun()  # 刷新畫面，會重新執行 load_data() 讀最新資料

# === 其餘部分不變（顯示清單、編輯、儲存按鈕等）===
st.markdown("### 📋 Project 清單")

display_df = df.copy()
today = date.today()
if not display_df.empty and "預計交付日期" in display_df.columns:
    display_df["剩餘天數"] = display_df["預計交付日期"].apply(
        lambda x: f"{(x - today).days} 天" if pd.notna(x) and (x - today).days >= 0
        else f"已逾期 {-(x - today).days} 天" if pd.notna(x) else "無日期"
    )
else:
    display_df["剩餘天數"] = "無日期"

edited_df = st.data_editor(
    display_df,
    column_config={
        "Project ID": st.column_config.TextColumn("Project ID", disabled=True),
        "Customer": st.column_config.TextColumn("Customer", required=True),
        "負責人": st.column_config.TextColumn("負責人", required=True),
        "預計交付日期": st.column_config.DateColumn("預計交付日期", required=True),
        "剩餘天數": st.column_config.TextColumn("剩餘天數", disabled=True),
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
)

if st.button("💾 儲存所有變更到雲端（表格編輯/刪除）"):
    final_df = edited_df.drop(columns=["剩餘天數"], errors="ignore")
    save_data(final_df)
    st.success("所有變更已儲存！")
    st.rerun()

# 統計與匯出（不變）
col1, col2, col3 = st.columns(3)
total = len(edited_df)
overdue = len(edited_df[edited_df["剩餘天數"].str.contains("逾期", na=False)]) if "剩餘天數" in edited_df.columns else 0
with col1: st.metric("總 Project 數", total)
with col2: st.metric("進行中", total - overdue)
with col3: st.metric("已逾期", overdue, delta_color="inverse")

st.download_button(
    label="📥 匯出為 CSV",
    data=edited_df.to_csv(index=False).encode("utf-8"),
    file_name=f"YIP_SHING_Projects_{date.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.caption("新增 Project 會立即顯示在清單中 • 編輯表格後請點「儲存所有變更」")