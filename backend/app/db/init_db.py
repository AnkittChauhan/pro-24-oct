import os
import sqlite3
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_db_path() -> str:
    """Ensure data directory exists and return absolute SQLite database path."""
    db_path = settings.DB_PATH
    if not os.path.isabs(db_path):
        abs_path = os.path.abspath(db_path)
    else:
        abs_path = db_path
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    return abs_path

def ensure_schema(conn: sqlite3.Connection) -> None:
    """Initialize database tables and indexes for actuals and forecasts if not present."""
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

def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a configured SQLite connection with row dictionary access.
    Self-healing: always guarantees table schema is present even if cache.db was deleted.
    """
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency read/write
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    ensure_schema(conn)
    return conn

def init_db() -> None:
    """Explicit database schema initialization."""
    conn = get_db_connection()
    conn.close()
