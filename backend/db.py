import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "prices.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            platform TEXT NOT NULL,
            price INTEGER NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS click_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        platform TEXT,
        price INTEGER,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin_user (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    )
""")
    cur.execute("""
CREATE TABLE IF NOT EXISTS visitors (
    day TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0
)
""")

from werkzeug.security import generate_password_hash

def create_default_admin():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admin_user WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admin_user (username, password_hash) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123"))
        )



    conn.commit()
    conn.close()
