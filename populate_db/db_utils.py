"""Database utilities for inserting quotation records."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "quotations.db"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run initialise_db/create_db.py first.")
    return sqlite3.connect(DB_PATH)


def insert_quotation_single(conn: sqlite3.Connection, scripture_reference: str, quoted_from: str, source: str):
    """Insert a single-verse quotation record, ignoring duplicates."""
    conn.execute(
        "INSERT OR IGNORE INTO quotation_single (scripture_reference, quoted_from, source) VALUES (?, ?, ?)",
        (scripture_reference, quoted_from, source),
    )


def insert_quotation_range(conn: sqlite3.Connection, scripture_reference: str, quoted_from: str, source: str):
    """Insert a range quotation record, ignoring duplicates."""
    conn.execute(
        "INSERT OR IGNORE INTO quotation_range (scripture_reference, quoted_from, source) VALUES (?, ?, ?)",
        (scripture_reference, quoted_from, source),
    )
