import os
import sqlite3
from typing import Generator
from app.core.config import settings

def get_db_path() -> str:
    """Ensure data directory exists and return absolute SQLite database path."""
    db_path = settings.DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    return db_path

def get_db_connection() -> sqlite3.Connection:
    """Create and return a configured SQLite connection with row dictionary access."""
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency read/write
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db() -> None:
    """Initialize database tables and indexes for actuals and forecasts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Actuals Table (Half-hourly National Wind Generation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS actuals (
        start_time TEXT PRIMARY KEY,
        publish_time TEXT,
        settlement_date TEXT NOT NULL,
        settlement_period INTEGER NOT NULL,
        generation_mw REAL NOT NULL,
        fetched_at TEXT NOT NULL
    );
    """)

    # Forecasts Table (WINDFOR Half-hourly Forecasts by Publish Timestamp)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        publish_time TEXT NOT NULL,
        start_time TEXT NOT NULL,
        generation_mw REAL NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (publish_time, start_time)
    );
    """)

    # High performance lookup indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_actuals_date ON actuals(settlement_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_actuals_period ON actuals(settlement_date, settlement_period);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_lookup ON forecasts(start_time, publish_time);")

    conn.commit()
    conn.close()
