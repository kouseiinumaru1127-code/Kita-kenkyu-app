import streamlit as st
import time
from supabase import create_client, Client

# --- Supabase接続 ---
SUPABASE_URL = "https://ttagggrpemnkkrfsgbyd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0YWdnZ3JwZW1ua2tyZnNnYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwOTMzMzQsImV4cCI6MjA5OTY2OTMzNH0.jbBD3eENhAgrwa1nTy4IM_ToHidGqR-ocXkzPlEOitQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 学習タイマー")

# --- セッションステートの初期化 ---
# タイマーが動いているかどうかの状態を保存する仕組みです
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- 1. ユーザー選択 ---
try:
    response = supabase.table("users").select("*").execute()
    users = response.data
except Exception as e:
    st.error(f"データ取得エラー: {e}")
    users = []

# データがない場合はここで処理を止めてエラーを防ぎます
if not users:
    st.warning("ユーザーデータが見つかりません。SupabaseのSQL EditorでINSERTを実行してください。")
    st.stop()

# ユーザー一覧をプルダウンにする
user_names = {u["name"]: u["id"] for u in users}
selected_user_name = st.selectbox("ユーザーを選択", list(user_names.keys()))
selected_user_id = user_names[selected_user_name]

# --- 2. タイマー機能 ---
st.subheader("⏱️ タイマー")

if not st.session_state.is_running:
    # 止まっている時：開始ボタンを表示
    if st.button("学習開始"):
        st.session_state.is_running = True
        st.session_state.start_time = time.time()
        st.rerun() # 画面を更新
else:
    # 動いている時：終了ボタンを表示
    st.info("学習中... 集中して頑張りましょう！")
    if st.button("学習終了"):
        st.session_state.is_running = False
        end_time = time.time()
        # かかった時間（秒）を計算
        duration = int(end_time - st.session_state.start_time)
        st.session_state.start_time = None
        
        st.success(f"お疲れ様でした！学習時間は {duration} 秒でした。記録を保存します。")
        
        # データベースに保存
        data = {
            "user_id": selected_user_id,
            "duration_seconds": duration,
            "category": "数学" # とりあえず最初は「数学」で固定
        }
        try:
            supabase.table("study_logs").insert(data).execute()
            st.write("✅ 記録が保存されました！")
        except Exception as e:
            st.error(f"保存失敗: {e}")

# --- 3. 記録表示 ---
st.subheader("📊 現在の学習記録")
try:
    logs = supabase.table("study_logs").select("*, users(name)").execute().data
    if logs:
        st.dataframe(logs) # 表形式で綺麗に表示
    else:
        st.write("まだ記録はありません。")
except Exception as e:
    st.write("記録の読み込みに失敗しました。")
```

これで、あなたが「学習終了」を押すまで時間が測れる、ちゃんとしたタイマーになります。ぜひ試してみてください！
