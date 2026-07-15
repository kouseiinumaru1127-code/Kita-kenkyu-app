import streamlit as st
import time
from supabase import create_client, Client

# --- 設定（あなたのSupabaseキーをここに入れてください） ---
SUPABASE_URL = "https://ttagggrpemnkkrfsgbyd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0YWdnZ3JwZW1ua2tyZnNnYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwOTMzMzQsImV4cCI6MjA5OTY2OTMzNH0.jbBD3eENhAgrwa1nTy4IM_ToHidGqR-ocXkzPlEOitQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 学習タイマー")

# 1. ユーザー選択
users = supabase.table("users").select("*").execute().data
user_names = {u["name"]: u["id"] for u in users}
selected_user = st.selectbox("ユーザーを選択", list(user_names.keys()))

# 2. タイマー機能
if st.button("学習開始"):
    with st.spinner("学習中...（終わったら下のボタンを押してね）"):
        time.sleep(5)  # テスト用に5秒だけ待つ設定
        
    st.success("終了！記録を保存します")
    
    # Supabaseに保存
    data = {
        "user_id": user_names[selected_user],
        "duration_seconds": 5,
        "category": "数学"
    }
    supabase.table("study_logs").insert(data).execute()
    st.write("記録が保存されました！")

# 3. 記録表示
st.subheader("現在の学習記録")
logs = supabase.table("study_logs").select("*, users(name)").execute().data
st.write(logs)
