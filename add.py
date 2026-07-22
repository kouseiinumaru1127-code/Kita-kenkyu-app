import streamlit as st
import time
import pandas as pd
from supabase import create_client, Client

# --- 設定 ---
SUPABASE_URL = "https://ttagggrpemnkkrfsgbyd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0YWdnZ3JwZW1ua2tyZnNnYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQwOTMzMzQsImV4cCI6MjA5OTY2OTMzNH0.jbBD3eENhAgrwa1nTy4IM_ToHidGqR-ocXkzPlEOitQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📚 学習タイマー")

# --- 1. ユーザー登録機能 ---
with st.expander("👤 新規ユーザー登録はこちら"):
    new_user_name = st.text_input("あなたの名前を入力してください")
    if st.button("ユーザーを登録"):
        if new_user_name:
            try:
                supabase.table("users").insert({"name": new_user_name}).execute()
                st.success(f"「{new_user_name}」さんを登録しました！")
                st.rerun()
            except Exception as e:
                st.error(f"登録に失敗しました: {e}")
        else:
            st.warning("名前を入力してください。")

# --- 2. ユーザー選択 ---
try:
    response = supabase.table("users").select("*").execute()
    users = response.data
    
    if not users:
        st.warning("ユーザーデータが見つかりません。上のフォームからユーザーを登録してください。")
        user_names = {}
    else:
        user_names = {u["name"]: u["id"] for u in users}
    
    if user_names:
        selected_user_name = st.selectbox("ユーザーを選択", list(user_names.keys()))
        selected_user_id = user_names[selected_user_name]
    else:
        selected_user_id = None

except Exception as e:
    st.error(f"データ取得エラー: {e}")
    selected_user_id = None

# --- 3. タイマー機能 ---
if selected_user_id:
    st.subheader("⏱️ タイマー")
    
    # ユーザーが自分で科目を追加する機能
    with st.expander("➕ 新しい科目を自分で追加する"):
        new_subject = st.text_input("追加したいオリジナル科目名（例：基本情報、TOEICなど）")
        if st.button("科目を追加"):
            if new_subject:
                try:
                    supabase.table("subjects").insert({"user_id": selected_user_id, "name": new_subject}).execute()
                    st.success(f"「{new_subject}」を追加しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"追加失敗: {e}")
            else:
                st.warning("科目名を入力してください。")
    
    # タイマーの状態を保持
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    # デフォルト科目 ＋ 自分が追加した科目を取得
    default_categories = ["数学", "英語", "国語", "理科", "社会", "プログラミング", "読書", "その他"]
    try:
        custom_subjects_data = supabase.table("subjects").select("name").eq("user_id", selected_user_id).execute().data
        custom_subjects = [s["name"] for s in custom_subjects_data] if custom_subjects_data else []
    except:
        custom_subjects = []

    categories = list(dict.fromkeys(default_categories + custom_subjects))
    
    # タイマー作動中は科目を変更できないようにロック
    selected_category = st.selectbox("学習する科目を選んでください", categories, disabled=st.session_state.is_running)

    if not st.session_state.is_running:
        if st.button("学習開始！", type="primary"):
            st.session_state.is_running = True
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        elapsed_seconds = int(time.time() - st.session_state.start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        st.info(f"⏳ 勉強中... 経過時間: **{minutes}分 {seconds}秒**")
        
        if st.button("学習終了！記録を保存", type="primary"):
            duration = int(time.time() - st.session_state.start_time)
            st.session_state.is_running = False
            st.session_state.start_time = None
            
            data = {
                "user_id": selected_user_id,
                "duration_seconds": duration,
                "category": selected_category
            }
            try:
                supabase.table("study_logs").insert(data).execute()
                st.success(f"{duration}秒間の学習を記録しました！")
                st.rerun()
            except Exception as e:
                st.error(f"保存失敗: {e}")

# --- 4. 記録表示 ＆ ランキング（左右分割ダッシュボード） ---
st.divider()
st.subheader("📊 学習データ・ランキング")

try:
    logs = supabase.table("study_logs").select("*, users(name)").execute().data
    if logs:
        df = pd.DataFrame(logs)
        # users(name) の入れ子構造から名前を取り出す
        df["user_name"] = df["users"].apply(lambda x: x["name"] if isinstance(x, dict) else "不明")
        
        # 画面を左右に分割
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 ユーザー別 合計学習時間")
            # ユーザーごとの合計秒数を計算
            ranking_df = df.groupby("user_name")["duration_seconds"].sum().reset_index()
            ranking_df["学習時間(分)"] = (ranking_df["duration_seconds"] / 60).round(1)
            ranking_df = ranking_df.sort_values(by="duration_seconds", ascending=False)
            st.dataframe(ranking_df[["user_name", "学習時間(分)"]], hide_index=True)
            
        with col2:
            st.markdown("### 📈 ユーザー別 グラフ")
            chart_data = ranking_df.set_index("user_name")["学習時間(分)"]
            st.bar_chart(chart_data)
            
        with st.expander("📝 すべての履歴を見る"):
            st.write(df[["user_name", "category", "duration_seconds", "created_at"]])
    else:
        st.write("まだ学習記録はありません。タイマーを動かして記録を残しましょう！")
except Exception as e:
    st.write(f"記録の読み込みに失敗しました: {e}")
