import streamlit as st
import pandas as pd
import requests
import json
from datetime import date, timedelta

# === 從 Secrets 讀取 GitHub 資訊 ===
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GIST_ID = st.secrets["GIST_ID"]
GIST_FILENAME = "yip_shing_projects.json"
API_URL = f"https://api.github.com/gists/{GIST_ID}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# === 讀取資料從 GitHub Gist ===
@st.cache_data(ttl=60)  # 每分鐘重新讀取一次
def load_data():
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        gist = response.json()
        file_content = gist["files"][GIST_FILENAME]["content"]
        data = json.loads(file_content)
        df = pd.DataFrame(data)
        # 確保日期欄位為 date 類型
        if "預計交付日期" in df.columns:
            df["預計交付日期"] = pd.to_datetime(df["預計交付日期"]).dt.date
        return df
    except Exception as e:
        st.error(f"載入資料失敗：{e}")
        # 失敗時返回空 DataFrame
        return pd.DataFrame(columns=["Project ID", "Customer", "負責人", "預計交付日期"])


# === 儲存資料到 GitHub Gist ===
def save_data(df):
    try:
        # 轉換日期為字串（JSON 必須）
        df_save = df.copy()
        if "預計交付日期" in df_save.columns:
            df_save["預計交付日期"] = df_save["預計交付日期"].astype(str)

        content = df_save.to_dict(orient="records")
        payload = {
            "description": "YIP SHING Project Database - Auto updated",
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(content, indent=2, ensure_ascii=False)
                }
            }
        }
        response = requests.patch(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        st.success("資料已成功儲存到雲端！")
    except Exception as e:
        st.error(f"儲存失敗：{e}")


# === 主程式 ===
st.set_page_config(page_title="YIP SHING Project Database", layout="wide")
st.title("🗂️ YIP SHING Project Database（永久儲存版）")

df = load_data()

# === 側邊欄：新增 Project ===
st.sidebar.header("📝 新增 Project")
with st.sidebar.form("add_form", clear_on_submit=True):
    st.write("### 填寫以下資訊新增專案")
    new_id = st.text_input("Project ID*", placeholder="YIP-004")
    new_customer = st.text_input("Customer*", placeholder="客戶名稱")
    new_manager = st.text_input("負責人*", placeholder="負責人姓名")
    new_date = st.date_input(
        "預計交付日期 (Lead Time)*",
        value=date.today() + timedelta(days=60),
        min_value=date.today()
    )
    submitted = st.form_submit_button("✨ 新增 Project")

    if submitted:
        if new_id and new_customer and new_manager:
            if new_id in df["Project ID"].values:
                st.error("Project ID 已存在！")
            else:
                new_row = pd.DataFrame([{
                    "Project ID": new_id,
                    "Customer": new_customer,
                    "負責人": new_manager,
                    "預計交付日期": new_date
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.rerun()
        else:
            st.error("請填寫所有必填欄位")

# === 顯示與編輯表格 ===
st.markdown("### 📋 Project 清單")

# 計算剩餘天數
display_df = df.copy()
today = date.today()
display_df["剩餘天數"] = display_df["預計交付日期"].apply(
    lambda x: f"{(x - today).days} 天" if (x - today).days >= 0 else f"已逾期 {-(x - today).days} 天"
)

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

# 儲存按鈕
if st.button("💾 儲存所有變更到雲端"):
    # 移除輔助欄位後儲存
    final_df = edited_df.drop(columns=["剩餘天數"], errors="ignore")
    save_data(final_df)
    st.rerun()

# === 統計與匯出 ===
col1, col2, col3 = st.columns(3)
total = len(edited_df)
overdue = len(edited_df[edited_df["剩餘天數"].str.contains("逾期", na=False)])
with col1: st.metric("總 Project", total)
with col2: st.metric("進行中", total - overdue)
with col3: st.metric("已逾期", overdue, delta_color="inverse")

st.download_button(
    "📥 匯出 CSV",
    data=edited_df.to_csv(index=False).encode("utf-8"),
    file_name=f"YIP_SHING_Projects_{date.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.caption("資料永久儲存在 GitHub Gist • 每次編輯後請點「儲存所有變更到雲端」")