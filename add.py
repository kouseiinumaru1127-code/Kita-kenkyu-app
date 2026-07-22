import streamlit as st
import time
from supabase import create_client, Client

# --- 設定 ---
SUPABASE_URL = "https://ttagggrpemnkkrfsgbyd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0YWdnZ3JwZW1ua2tyZnNnYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwOTMzMzQsImV4cCI6MjA5OTY2OTMzNH0.jbBD3eENhAgrwa1nTy4IM_ToHidGqR-ocXkzPlEOitQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 学習タイマー")

# --- 1. 新規ユーザー登録 ---
st.subheader("👤 新規ユーザー登録")
new_user_name = st.text_input("あなたの名前を入力してください")
if st.button("ユーザーを登録"):
    if new_user_name:
        try:
            # usersテーブルに名前を保存
            supabase.table("users").insert({"name": new_user_name}).execute()
            st.success(f"「{new_user_name}」さんを登録しました！")
            st.rerun() # 画面をリロードして下のリストにすぐ反映させます
        except Exception as e:
            st.error(f"登録に失敗しました: {e}")
    else:
        st.warning("名前を入力してください。")

st.divider() # 区切り線

# --- 2. ユーザー選択 ---
try:
    response = supabase.table("users").select("*").execute()
    users = response.data
    
    if not users:
        st.info("まだユーザーが登録されていません。上のフォームから登録してください。")
        selected_user_id = None
    else:
        user_names = {u["name"]: u["id"] for u in users}
        selected_user_name = st.selectbox("学習を記録するユーザーを選択", list(user_names.keys()))
        selected_user_id = user_names[selected_user_name]

except Exception as e:
    st.error(f"データ取得エラー: {e}")
    selected_user_id = None

# --- 3. タイマー機能 ---
if selected_user_id:
    st.subheader("⏱️ タイマー")
    
    # タイマーが動いているかどうかの状態を保存
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    if not st.session_state.is_running:
        # 止まっている時：開始ボタン
        if st.button("学習開始！", type="primary"):
            st.session_state.is_running = True
            st.session_state.start_time = time.time() # 現在の時刻を記録
            st.rerun()
    else:
        # 動いている時：終了ボタン
        st.info("🔥 学習中... 集中して頑張りましょう！")
        if st.button("学習終了して記録を保存", type="primary"):
            st.session_state.is_running = False
            end_time = time.time()
            
            # 終了時刻から開始時刻を引いて、かかった時間（秒）を計算
            duration = int(end_time - st.session_state.start_time)
            st.session_state.start_time = None
            
            st.success(f"お疲れ様でした！学習時間は {duration} 秒でした。")
            
            # Supabaseに保存
            data = {
                "user_id": selected_user_id,
                "duration_seconds": duration,
                "category": "数学" # 最初は「数学」で固定しておきます
            }
            try:
                supabase.table("study_logs").insert(data).execute()
                st.write("✅ 記録が保存されました！")
            except Exception as e:
                st.error(f"保存失敗: {e}")

st.divider()

# --- 4. 記録表示 ---
st.subheader("📊 現在の学習記録")
try:
    # 記録を最新順（created_atの降順）で取得
    logs = supabase.table("study_logs").select("*, users(name)").order("created_at", desc=True).execute().data
    if logs:
        # 見やすいようにデータを整理
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "名前": log["users"]["name"],
                "学習時間(秒)": log["duration_seconds"],
                "カテゴリー": log["category"],
                "日時": log["created_at"][:19].replace("T", " ")
            })
        st.dataframe(formatted_logs)
    else:
        st.write("まだ記録はありません。学習を開始してみましょう！")
except Exception as e:
    st.write("記録の読み込みに失敗しました。")
