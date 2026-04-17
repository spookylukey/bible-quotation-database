#!/usr/bin/env python3
"""Create (or recreate) the SQLite database from schema.sql."""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "quotations.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def create_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Deleted existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    schema = SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.close()
    print(f"Created database: {DB_PATH}")


if __name__ == "__main__":
    create_db()
