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

# --- 3. タイマー機能（通常 ＆ ポモドーロ切り替え） ---
if selected_user_id:
    st.subheader("⏱️ タイマー")
    
    # タイマーモードの選択
    timer_mode = st.radio("タイマーのモードを選んでください", ["通常ストップウォッチ", "ポモドーロ（集中25分 / 休憩5分）"], horizontal=True)
    
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
    
    # デフォルト科目 ＋ 自分が追加した科目を取得
    default_categories = ["数学", "英語", "国語", "理科", "社会", "プログラミング", "読書", "その他"]
    try:
        custom_subjects_data = supabase.table("subjects").select("id, name").eq("user_id", selected_user_id).execute().data
        custom_subjects = [s["name"] for s in custom_subjects_data] if custom_subjects_data else []
    except:
        custom_subjects = []

    categories = list(dict.fromkeys(default_categories + custom_subjects))
    
    # セッション状態の初期化
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "pomo_phase" not in st.session_state:
        st.session_state.pomo_phase = "study" # "study" (集中25分) または "break" (休憩5分)

    # タイマー作動中は科目を変更できないようにロック
    selected_category = st.selectbox("学習する科目を選んでください", categories, disabled=st.session_state.is_running)

    # --- モード別の処理 ---
    if timer_mode == "通常ストップウォッチ":
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

    else:
        # ポモドーロモード（集中25分 = 1500秒、休憩5分 = 300秒）
        STUDY_TIME = 25 * 60
        BREAK_TIME = 5 * 60

        if not st.session_state.is_running:
            if st.button("ポモドーロ開始（25分集中）", type="primary"):
                st.session_state.is_running = True
                st.session_state.start_time = time.time()
                st.session_state.pomo_phase = "study"
                st.rerun()
        else:
            elapsed = int(time.time() - st.session_state.start_time)
            
            if st.session_state.pomo_phase == "study":
                remaining = STUDY_TIME - elapsed
                if remaining > 0:
                    rem_min = remaining // 60
                    rem_sec = remaining % 60
                    st.info(f"🍅 **集中タイム中！** 残り時間: **{rem_min}分 {rem_sec}秒**")
                    # 画面を自動で1秒ごとに更新させるためのリロード（Streamlitの仕組み）
                    time.sleep(1)
                    st.rerun()
                else:
                    # 25分終了 -> 休憩フェーズへ移行（自動で25分分をデータベースに記録！）
                    try:
                        data = {
                            "user_id": selected_user_id,
                            "duration_seconds": STUDY_TIME,
                            "category": selected_category
                        }
                        supabase.table("study_logs").insert(data).execute()
                        st.success("🎉 25分集中達成！自動で記録しました。次は5分間の休憩です！")
                    except Exception as e:
                        st.error(f"自動保存失敗: {e}")
                    
                    st.session_state.pomo_phase = "break"
                    st.session_state.start_time = time.time()
                    st.rerun()
            
            else:
                # 休憩フェーズ（5分）
                remaining = BREAK_TIME - elapsed
                if remaining > 0:
                    rem_min = remaining // 60
                    rem_sec = remaining % 60
                    st.warning(f"☕ **休憩タイム中...** 残り時間: **{rem_min}分 {rem_sec}秒**")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success("☕ 休憩終了！お疲れ様でした。")
                    st.session_state.is_running = False
                    st.session_state.start_time = None
                    st.session_state.pomo_phase = "study"
                    st.rerun()

            # ポモドーロを途中で中断したいとき用
            if st.button("ポモドーロを中断する"):
                st.session_state.is_running = False
                st.session_state.start_time = None
                st.session_state.pomo_phase = "study"
                st.rerun()

# --- 4. 記録表示 ＆ ランキング（左右分割ダッシュボード） ---
st.divider()
st.subheader("📊 学習データ・ランキング")

try:
    logs = supabase.table("study_logs").select("*, users(name)").execute().data
    if logs:
        df = pd.DataFrame(logs)
        df["user_name"] = df["users"].apply(lambda x: x["name"] if isinstance(x, dict) else "不明")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 ユーザー別 合計学習時間")
            ranking_df = df.groupby("user_name")["duration_seconds"].sum().reset_index()
            ranking_df["学習時間(分)"] = (ranking_df["duration_seconds"] / 60).round(1)
            ranking_df = ranking_df.sort_values(by="duration_seconds", ascending=False)
            st.dataframe(ranking_df[["user_name", "学習時間(分)"]], hide_index=True)
            
        with col2:
            st.markdown("### 📈 ユーザー別 グラフ")
            chart_data = ranking_df.set_index("user_name")["学習時間(分)"]
            st.bar_chart(chart_data)
            
        with st.expander("📝 すべての履歴を見る・削除する"):
            st.write("間違えて記録してしまったデータを個別に削除できます。")
            for index, row in df.iterrows():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.text(f"👤 {row['user_name']} | 📖 {row['category']} | ⏱️ {row['duration_seconds']}秒 | 📅 {row['created_at']}")
                with col_b:
                    if st.button("削除", key=f"del_log_{row['id']}"):
                        try:
                            supabase.table("study_logs").delete().eq("id", row['id']).execute()
                            st.success("履歴を削除しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"削除失敗: {e}")
    else:
        st.write("まだ学習記録はありません。タイマーを動かして記録を残しましょう！")
except Exception as e:
    st.write(f"記録の読み込みに失敗しました: {e}")

# --- 5. ユーザー・科目の管理（削除機能） ---
st.divider()
with st.expander("⚙️ ユーザー・科目の管理（削除）"):
    tab1, tab2 = st.tabs(["👤 ユーザー削除", "📚 追加した科目の削除"])
    
    with tab1:
        st.write("登録されているユーザーを削除します。（※関連する学習記録も一緒に削除されます）")
        try:
            users_res = supabase.table("users").select("*").execute().data
            if users_res:
                user_del_dict = {u["name"]: u["id"] for u in users_res}
                target_user = st.selectbox("削除するユーザーを選んでください", list(user_del_dict.keys()), key="del_user_select")
                if st.button("このユーザーを削除する", type="primary"):
                    try:
                        supabase.table("users").delete().eq("id", user_del_dict[target_user]).execute()
                        st.success(f"ユーザー「{target_user}」を削除しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除失敗: {e}")
            else:
                st.write("登録されているユーザーがいません。")
        except Exception as e:
            st.write(f"ユーザー一覧の取得に失敗しました: {e}")
            
    with tab2:
        st.write("自分で追加したオリジナル科目を削除します。")
        try:
            subs_res = supabase.table("subjects").select("*, users(name)").execute().data
            if subs_res:
                sub_list = []
                for s in subs_res:
                    u_name = s["users"]["name"] if isinstance(s.get("users"), dict) else "不明"
                    sub_list.append({"label": f"{s['name']} (登録者: {u_name})", "id": s["id"]})
                
                sub_labels = [item["label"] for item in sub_list]
                target_sub_label = st.selectbox("削除する科目を選んでください", sub_labels, key="del_sub_select")
                
                if st.button("この科目を削除する", type="primary"):
                    target_id = next(item["id"] for item in sub_list if item["label"] == target_sub_label)
                    try:
                        supabase.table("subjects").delete().eq("id", target_id).execute()
                        st.success("科目を削除しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除失敗: {e}")
            else:
                st.write("追加されたオリジナル科目はありません。")
        except Exception as e:
            st.write(f"科目一覧の取得に失敗しました: {e}")
