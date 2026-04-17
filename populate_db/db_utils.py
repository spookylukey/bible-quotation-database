"""Database utilities for inserting quotation records."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "quotations.db"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run initialise_db/create_db.py first.")
    return sqlite3.connect(DB_PATH)


def insert_quotation(conn: sqlite3.Connection, scripture_reference: str, quoted_from: str, source: str):
    """Insert a single quotation record, ignoring duplicates."""
    conn.execute(
        "INSERT OR IGNORE INTO quotation (scripture_reference, quoted_from, source) VALUES (?, ?, ?)",
        (scripture_reference, quoted_from, source),
    )


def insert_quotation_pairs(
    conn: sqlite3.Connection,
    scripture_refs: list[str],
    quoted_from_refs: list[str],
    source: str,
) -> int:
    """Insert all combinations of scripture_refs x quoted_from_refs.

    Returns the number of rows inserted.
    """
    count = 0
    for sr in scripture_refs:
        for qf in quoted_from_refs:
            conn.execute(
                "INSERT OR IGNORE INTO quotation (scripture_reference, quoted_from, source) VALUES (?, ?, ?)",
                (sr, qf, source),
            )
            count += conn.total_changes  # approximate
    return count
