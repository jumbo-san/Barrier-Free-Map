import sqlalchemy
from sqlalchemy import text
import pandas as pd
import streamlit as st
import os

@st.cache_resource
def get_engine():
    try:
        url = st.secrets["SUPABASE_URL"]
    except:
        url = os.environ.get("SUPABASE_URL", "")

    engine = sqlalchemy.create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10
    )
    return engine

# テーブルを作成する関数
def create_table():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pins (
                id SERIAL PRIMARY KEY,
                場所名 TEXT NOT NULL,
                種類 TEXT NOT NULL,
                緯度 FLOAT NOT NULL,
                経度 FLOAT NOT NULL,
                備考 TEXT,
                投稿日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS official_pins (
                id SERIAL PRIMARY KEY,
                駅名 TEXT NOT NULL,
                事業者名 TEXT,
                路線名 TEXT,
                種類 TEXT NOT NULL,
                緯度 FLOAT NOT NULL,
                経度 FLOAT NOT NULL,
                設置数 TEXT
            )
        """))

# CSVから公式ピンをDBに取り込む関数
def import_official_pins(csv_path):
    engine = get_engine()
    df = pd.read_csv(csv_path, encoding="cp932")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM official_pins"))

        for _, row in df.iterrows():
            try:
                緯度 = float(row["緯度"])
                経度 = float(row["経度"])
            except (ValueError, TypeError):
                continue

            駅名 = str(row["鉄道駅の名称"])
            事業者名 = str(row["鉄道事業者名"])
            路線名 = str(row["路線名"])
            エレベーター数 = str(row["エレベーターの設置基数"]).strip()
            傾斜路数 = str(row["傾斜路の設置箇所数"]).strip()

            if エレベーター数 not in ["-", "nan", ""]:
                conn.execute(text("""
                    INSERT INTO official_pins (駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数)
                    VALUES (:駅名, :事業者名, :路線名, :種類, :緯度, :経度, :設置数)
                """), {"駅名": 駅名, "事業者名": 事業者名, "路線名": 路線名,
                       "種類": "エレベーター", "緯度": 緯度, "経度": 経度, "設置数": エレベーター数})

            if 傾斜路数 not in ["-", "nan", ""]:
                conn.execute(text("""
                    INSERT INTO official_pins (駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数)
                    VALUES (:駅名, :事業者名, :路線名, :種類, :緯度, :経度, :設置数)
                """), {"駅名": 駅名, "事業者名": 事業者名, "路線名": 路線名,
                       "種類": "スロープ", "緯度": 緯度, "経度": 経度, "設置数": 傾斜路数})

# 表示範囲内の公式ピンを取得する関数
def get_official_pins_in_bounds(south, north, west, east):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数
            FROM official_pins
            WHERE 緯度 BETWEEN :south AND :north
            AND 経度 BETWEEN :west AND :east
        """), {"south": south, "north": north, "west": west, "east": east})
        return result.fetchall()

# 表示範囲内のユーザー投稿ピンを取得する関数
def get_reliability_scores_in_bounds(south, north, west, east):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                場所名,
                種類,
                COUNT(*) as 投稿数,
                AVG(緯度) as 平均緯度,
                AVG(経度) as 平均経度
            FROM pins
            WHERE 緯度 BETWEEN :south AND :north
            AND 経度 BETWEEN :west AND :east
            GROUP BY 場所名, 種類
        """), {"south": south, "north": north, "west": west, "east": east})
        return result.fetchall()

# データを一件追加する関数
def insert_pin(場所名, 種類, 緯度, 経度, 備考):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pins (場所名, 種類, 緯度, 経度, 備考)
            VALUES (:場所名, :種類, :緯度, :経度, :備考)
        """), {"場所名": 場所名, "種類": 種類, "緯度": 緯度, "経度": 経度, "備考": 備考})

# 全データを取得する関数
def get_all_pins():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM pins ORDER BY 投稿日時 DESC"))
        return result.fetchall()

# ピンの種類で取得する関数
def get_pin_by_types(種類):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM pins WHERE 種類 = :種類 ORDER BY 投稿日時 DESC
        """), {"種類": 種類})
        return result.fetchall()

# 場所名で投稿をグループ化して信頼性スコアを計算する関数
def get_reliability_scores():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                場所名,
                種類,
                COUNT(*) as 投稿数,
                AVG(緯度) as 平均緯度,
                AVG(経度) as 平均経度
            FROM pins
            GROUP BY 場所名, 種類
        """))
        return result.fetchall()

# create_table()は削除（初回のみ手動で実行）