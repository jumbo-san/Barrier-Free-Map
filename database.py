import pyodbc
import pandas as pd
import os

def get_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=barrier-free-server.database.windows.net;'
        'DATABASE=barrier-free-db;'
        'UID=じゃんぼ;'
        'PWD=' + os.environ.get("AZURE_DB_PASSWORD", "") + ';'
        'Encrypt=yes;'
        'TrustServerCertificate=no;'
    )
    return conn

# テーブルを作成する関数
def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    # ユーザー投稿テーブルの作成
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pins' AND xtype='U')
        CREATE TABLE pins (
            id INT PRIMARY KEY IDENTITY(1,1),
            場所名 NVARCHAR(255) NOT NULL,
            種類 NVARCHAR(50) NOT NULL,
            緯度 FLOAT NOT NULL,
            経度 FLOAT NOT NULL,
            備考 NVARCHAR(1000),
            投稿日時 DATETIME DEFAULT GETDATE()
        )
    """)

    # 公式データテーブルの作成
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='official_pins' AND xtype='U')
        CREATE TABLE official_pins (
            id INT PRIMARY KEY IDENTITY(1,1),
            駅名 NVARCHAR(255) NOT NULL,
            事業者名 NVARCHAR(255),
            路線名 NVARCHAR(255),
            種類 NVARCHAR(50) NOT NULL,
            緯度 FLOAT NOT NULL,
            経度 FLOAT NOT NULL,
            設置数 NVARCHAR(50)
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
        try:
            緯度 = float(row["緯度"])
            経度 = float(row["経度"])
        except (ValueError, TypeError):
            continue

        駅名 = row["鉄道駅の名称"]
        事業者名 = row["鉄道事業者名"]
        路線名 = row["路線名"]
        エレベーター数 = str(row["エレベーターの設置基数"]).strip()
        傾斜路数 = str(row["傾斜路の設置箇所数"]).strip()

        if エレベーター数 not in ["-", "nan", ""]:
            cursor.execute("""
                INSERT INTO official_pins (駅名, 事業者名, 路線名, 種類, 緯度, 経度, 設置数)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (駅名, 事業者名, 路線名, "エレベーター", 緯度, 経度, エレベーター数))

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
        INSERT INTO pins (場所名, 種類, 緯度, 経度, 備考)
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