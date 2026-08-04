import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import folium
from streamlit_folium import st_folium
import database
import time

st.set_page_config(page_title="投稿する", layout="centered")

st.title("バリアフリー情報を投稿する")
st.caption("知ってる場所のエレベーターまたはスロープ情報を投稿してください")

def get_coordinates(place_name):
    try:
        geolocator = Nominatim(user_agent="barrier_free_map")
        location = geolocator.geocode(place_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None

st.markdown("#### 場所の指定方法を選択してください")

method = st.radio(
    "形式",
    ["名前で検索する", "地図にピンを立てる"],
    horizontal=True
)

lat, lon = None, None
spot_name = ""

if method == "名前で検索する":
    st.markdown("#### 場所名を入力してください")
    spot_name = st.text_input(
        "場所の名前",
        placeholder="例：東京駅"
    )

    if spot_name:
        with st.spinner("座標を取得中..."):
            lat, lon = get_coordinates(spot_name)
            time.sleep(1)

        if lat and lon:
            st.success(f"座標を取得しました：緯度{lat:.4f}、経度{lon:.4f}")

            st.caption("取得した座標の確認マップ")
            confirm_map = folium.Map(location=[lat, lon], zoom_start=17)
            folium.Marker(
                location=[lat, lon],
                tooltip=spot_name,
                icon=folium.Icon(color="red", icon="map-marker")
            ).add_to(confirm_map)
            st_folium(
                confirm_map,
                use_container_width=True,
                height=200,
                key="confirm_map"
            )
        else:
            st.error("座標の取得に失敗しました。場所の名前を確認してください。")

else:
    st.markdown("#### 地図をクリックしてピンを立ててください")
    st.caption("ピンを立てた後、下の場所名欄に場所名を入力してください")

    click_map = folium.Map(
        location=[35.4198, 136.2657],
        zoom_start=15,
    )

    map_data = st_folium(
        click_map,
        use_container_width=True,
        height=350,
        key="click_map"
    )

    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        st.success(f"座標を取得しました：緯度{lat:.4f}、経度{lon:.4f}")
    else:
        st.info("地図をクリックして場所を指定してください")

    spot_name = st.text_input(
        "場所の名前",
        placeholder="例：東京駅"
    )

st.divider()
st.markdown("#### ピンの種類")

pin_type = st.radio(
    "種類を選んでください",
    ["エレベーター", "スロープ"],
    horizontal=True
)

st.markdown("#### 備考(任意)")
note = st.text_area(
    "詳細情報",
    placeholder="例：北口改札横にあります。",
    height=100
)

st.divider()

if st.button("投稿する", type="primary", use_container_width=True):
    if not spot_name:
        st.error("場所の名前を入力してください")
    elif not lat or not lon:
        st.error("座標が取得できていません。場所名を確認してください")
    else:
        database.insert_pin(spot_name, pin_type, lat, lon, note)
        st.success(f"「{spot_name}」の{pin_type}情報を投稿しました！")
        st.balloons()
        time.sleep(2)
        st.switch_page("app.py")