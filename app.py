import streamlit as st
import folium
from streamlit_folium import st_folium
import database
import score


# ページ設定
st.set_page_config(
    page_title="バリアフリーマップ", 
    layout="wide",
    initial_sidebar_state="collapsed"
    )

# CSSで余白を減らす→地図を画面いっぱいに
st.markdown("""
            <style>
                .block-container {
                    padding-top: 0.5rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                header { visibility: hidden; }
            </style>
""", unsafe_allow_html=True)

# フィルターとほかのページのリンク
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    show_elevater = st.checkbox("エレベーター", value=True)
    show_slope = st.checkbox("スロープ", value=True)
with col2:
    st.page_link("pages/1_投稿.py", label="投稿する", use_container_width=True)
with col3:
    st.page_link("pages/2_一覧.py", label="投稿一覧を見る", use_container_width=True)

# 地図作成
m = folium.Map(
    location=[35.4198, 136.2657], 
    zoom_start=15  
)
# 信頼性をピンに表示
reliability_data = database.get_reliability_scores()

for data in reliability_data:
    場所名 = data[0]
    種類 = data[1]
    投稿数 = data[2]
    緯度 = data[3]
    経度 = data[4]

    # フィルタリング部分
    if 種類 == "エレベーター" and not show_elevater:
        continue
    if 種類 == "スロープ" and not show_slope:
        continue

     #　信頼性を判定
    color = "blue" if 種類 == "エレベーター" else "green"
    icon = "arrow-up" if 種類 == "エレベーター" else "transfer"
    status = score.judge_reliability(投稿数)
    status_icon = score.get_status_icon(status)

    icon_emoji = "🛗" if 種類 == "エレベーター" else "👨‍🦽"
    popup_text = f"""
    <b>{場所名}</b><br>
    {icon_emoji}{種類}<br>
    投稿数：{投稿数}件 {status_icon}
    """

    folium.Marker(
        location=[緯度, 経度],
        popup=folium.Popup(popup_text, max_width=200),
        tooltip=f"{icon_emoji}{場所名}",
        icon=folium.Icon(color=color, icon=icon)
    ).add_to(m)

# 凡例
st.caption("🔵　エレベーター　🟢　スロープ　✅確認済み　🔄確認中")

st_folium(m, use_container_width=True, height=650)