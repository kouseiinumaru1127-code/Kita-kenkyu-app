import streamlit as st
from supabase import create_client, Client

# --- 1. Supabaseの接続設定 ---
# さきほどメモした2つを、以下の "" の中に貼り付けてください。
SUPABASE_URL = "https://ttagggrpemnkkrfsgbyd.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0YWdnZ3JwZW1ua2tyZnNnYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwOTMzMzQsImV4cCI6MjA5OTY2OTMzNH0.jbBD3eENhAgrwa1nTy4IM_ToHidGqR-ocXkzPlEOitQ"

# 接続クライアントを作成
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("接続テスト画面")

# --- 2. データの取得テスト ---
st.write("Supabaseからデータを取得しています...")

try:
    # 先ほど作成した users テーブルからデータを取得
    response = supabase.table("users").select("*").execute()
    
    # 取得したデータを画面に表示
    st.success("✅ Supabaseへの接続とデータの取得に成功しました！")
    st.write("▼ users テーブルの中身:")
    st.json(response.data)

except Exception as e:
    st.error("❌ 接続に失敗しました。URLとAPI Keyを確認してください。")
    st.write(f"エラーの詳細: {e}")
