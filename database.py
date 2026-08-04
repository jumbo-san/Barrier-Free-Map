import sqlite3
import pandas as pd

def get_connection():
    conn = sqlite3.connect("spots.db")
    return conn

# テーブルを作成する関数
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    # ユーザー投稿テーブルの作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            場所名 TEXT NOT NULL,
            種類 TEXT NOT NULL,
            緯度 REAL NOT NULL,
            経度 REAL NOT NULL,
            備考 TEXT,
            投稿日時 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 公式データテーブルの作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS official_pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            駅名 TEXT NOT NULL,
            事業者名 TEXT,
            路線名 TEXT,
            種類 TEXT NOT NULL,
            緯度 REAL NOT NULL,
            経度 REAL NOT NULL,
            設置数 TEXT
        )
    """)

    conn.commit()
    conn.close()

# CSVから公式ピンをDBに取り込む関数
def import_official_pins(csv_path):
    conn = get_connection()
    cursor = conn.cursor()

    # 既存データを削除（重複防止）
    cursor.execute("DELETE FROM official_pins")

    df = pd.read_csv(csv_path, encoding="cp932")

    for _, row in df.iterrows():
        緯度 = row["緯度"]
        経度 = row["経度"]
        駅名 = row["鉄道駅の名称"]
        事業者名 = row["鉄道事業者名"]
        路線名 = row["路線名"]
        エレベーター数 = str(row["エレベーターの設置基数"]).strip()
        傾斜路数 = str(row["傾斜路の設置箇所数"]).strip()

        # 緯度経度が無効な行はスキップ
        try:
            緯度 = float(緯度)
            経度 = float(経度)
        except (ValueError, TypeError):
            continue

        # エレベーターがある駅
        if エレベーター数 not in ["-", "nan", ""]:
            cursor.execute("""
                INSERT INTO official_pins (駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (駅名, 事業者名, 路線名, "エレベーター", 緯度, 経度, エレベーター数))

        # スロープ（傾斜路）がある駅
        if 傾斜路数 not in ["-", "nan", ""]:
            cursor.execute("""
                INSERT INTO official_pins (駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (駅名, 事業者名, 路線名, "スロープ", 緯度, 経度, 傾斜路数))

    conn.commit()
    conn.close()

# 公式ピンを全件取得する関数
def get_official_pins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数 FROM official_pins")
    results = cursor.fetchall()
    conn.close()
    return results

# データを一件追加する関数
def insert_pin(場所名, 種類, 緯度, 経度, 備考):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pins 
        (場所名, 種類, 緯度, 経度, 備考)
        VALUES (?, ?, ?, ?, ?)
    """, (場所名, 種類, 緯度, 経度, 備考))
    conn.commit()
    conn.close()

# 全データを取得する関数
def get_all_pins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pins ORDER BY 投稿日時 DESC")
    pins = cursor.fetchall()
    conn.close() 
    return pins

# ピンの種類で取得する関数
def get_pin_by_types(種類):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pins WHERE 種類 = ? ORDER BY 投稿日時 DESC
    """, (種類,))
    pins = cursor.fetchall()
    conn.close()
    return pins

# 場所名で投稿をグループ化して信頼性スコアを計算する関数
def get_reliability_scores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            場所名,
            種類,
            COUNT(*) as 投稿数,
            AVG(緯度) as 平均緯度,
            AVG(経度) as 平均経度
        FROM pins
        GROUP BY 場所名, 種類
    """)
    results = cursor.fetchall()
    conn.close()
    return results

# アプリ起動時にテーブルを自動作成
create_table()