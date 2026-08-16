import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import database
import score
import os

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
    show_official = st.checkbox("公式データ（JR）", value=True)
with col2:
    st.page_link("pages/1_投稿.py", label="投稿する", use_container_width=True)
with col3:
    st.page_link("pages/2_一覧.py", label="投稿一覧を見る", use_container_width=True)

# デフォルトの表示範囲（初回表示時）
DEFAULT_BOUNDS = {
    "south": 35.38,
    "north": 35.46,
    "west": 136.22,
    "east": 136.32
}

# 地図の表示範囲をsession_stateで管理
if "bounds" not in st.session_state:
    st.session_state["bounds"] = DEFAULT_BOUNDS

bounds = st.session_state["bounds"]
south = bounds["south"]
north = bounds["north"]
west = bounds["west"]
east = bounds["east"]

# データをキャッシュして取得（TTL=60秒）
@st.cache_data(ttl=60)
def load_official_pins(south, north, west, east):
    return database.get_official_pins_in_bounds(south, north, west, east)

@st.cache_data(ttl=60)
def load_user_pins(south, north, west, east):
    return database.get_reliability_scores_in_bounds(south, north, west, east)

# 地図作成
m = folium.Map(
    location=[35.4198, 136.2657], 
    zoom_start=15  
)

# クラスタリンググループを作成
user_cluster = MarkerCluster(name="ユーザー投稿").add_to(m)
official_cluster = MarkerCluster(name="公式データ（JR）").add_to(m)

# 表示範囲内のユーザー投稿ピンを取得して表示
reliability_data = load_user_pins(south, north, west, east)

for data in reliability_data:
    場所名 = data[0]
    種類 = data[1]
    投稿数 = data[2]
    緯度 = data[3]
    経度 = data[4]

    if 種類 == "エレベーター" and not show_elevater:
        continue
    if 種類 == "スロープ" and not show_slope:
        continue

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
    ).add_to(user_cluster)

# 表示範囲内の公式ピンを取得して表示
if show_official:
    official_pins = load_official_pins(south, north, west, east)

    for pin in official_pins:
        駅名 = pin[0]
        事業者名 = pin[1]
        路線名 = pin[2]
        種類 = pin[3]
        緯度 = pin[4]
        経度 = pin[5]
        設置数 = pin[6]

        if 種類 == "エレベーター" and not show_elevater:
            continue
        if 種類 == "スロープ" and not show_slope:
            continue

        icon_emoji = "🛗" if 種類 == "エレベーター" else "👨‍🦽"
        popup_text = f"""
        <b>{駅名}駅</b><br>
        {icon_emoji}{種類}<br>
        {事業者名} / {路線名}<br>
        設置数：{設置数}<br>
        <span style='color:orange;'>🏛️ 公式データ</span>
        """

        folium.Marker(
            location=[緯度, 経度],
            popup=folium.Popup(popup_text, max_width=200),
            tooltip=f"🏛️{駅名}駅",
            icon=folium.Icon(color="orange", icon="info-sign")
        ).add_to(official_cluster)

# 凡例
st.caption("🔵　エレベーター（投稿）　🟢　スロープ（投稿）　🟠　公式データ（JR）　✅確認済み　🔄確認中")

# 地図を表示して表示範囲を取得
map_data = st_folium(m, use_container_width=True, height=650)

# 地図の表示範囲が変わったらsession_stateを更新して再描画
if map_data and map_data.get("bounds"):
    new_bounds = {
        "south": map_data["bounds"]["_southWest"]["lat"],
        "north": map_data["bounds"]["_northEast"]["lat"],
        "west": map_data["bounds"]["_southWest"]["lng"],
        "east": map_data["bounds"]["_northEast"]["lng"],
    }
    if new_bounds != st.session_state["bounds"]:
        st.session_state["bounds"] = new_bounds
        st.rerun()