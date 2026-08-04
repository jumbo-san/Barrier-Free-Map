import streamlit as st
import pandas as pd
import database
import score

st.set_page_config(page_title="スポット一覧", layout="wide")

st.title("登録スポット一覧")

# フィルタリング
col1, col2 = st.columns(2)
with col1:
    filter_type = st.selectbox(
        "種類で絞り込む",
        ["すべて", "エレベーター", "スロープ"]
    )
with col2:
    filter_status = st.selectbox(
        "信頼性で絞り込む",
        ["すべて", "✅確認済み", "🔄確認中"]
    )

st.divider()

st.markdown("#### 集計データ(信頼性スコア付き)")

reliability_data = database.get_reliability_scores()

if reliability_data:
    rows = []
    for data in reliability_data:
        場所名 = data[0]
        種類 = data[1]
        投稿数 = data[2]
        緯度 = data[3]
        経度 = data[4]

        status = score.judge_reliability(投稿数)
        status_icon = score.get_status_icon(status)

        if filter_type != "すべて" and 種類 != filter_type:
            continue
        if filter_status != "すべて" and status_icon != filter_status:
            continue

        rows.append({
            "場所名": 場所名,
            "種類": "🛗エレベーター" if 種類 == "エレベーター" else "👨‍🦽スロープ",
            "投稿数": 投稿数,
            "信頼性": status_icon,
            "緯度": round(緯度, 4),
            "経度": round(経度, 4),
        })

    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("条件に一致するスポットがありません。")

else:
    st.info("まだ投稿がありません。投稿画面から情報を追加してください。")

st.divider()

st.markdown("#### 全投稿データ")

all_pins = database.get_all_pins()
if all_pins:
    df = pd.DataFrame(all_pins, columns=[
        "ID", "場所名", "種類", "緯度", "経度", "備考", "投稿日時"
    ])
    df["種類"] = df["種類"].apply(
        lambda x: "🛗エレベーター" if x == "エレベーター" else "👨‍🦽スロープ"
    )
    st.dataframe(df, use_container_width=True)
else:
    st.info("まだ投稿がありません")

st.divider()
if st.button("地図に戻る", use_container_width=True):
    st.switch_page("app.py")