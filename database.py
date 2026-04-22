import sqlite3

def get_connection():
    conn = sqlite3.connect("spots.db")
    return conn

#　テーブルを作成する関数
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    
    #ユーザー投稿テーブルの作成
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

    conn.commit() #変更を保存
    conn.close() #接続を閉じる

#　データを一件追加する関数
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

#　全データを取得する関数
def get_all_pins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pins ORDER BY 投稿日時 DESC")
    pins = cursor.fetchall() #全行を取得
    conn.close() 
    return pins

# ぴの種類
def get_pin_by_types(種類):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pins WHERE 種類 = ? ORDER BY 投稿日時 DESC
    """, (種類,))
    pins = cursor.fetchall()
    conn.close()
    return pins

# 場所名で投稿をグループ化をして信頼性スコアを計算する関数
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

# アプリ起動時にテーブルを自動更新
create_table()