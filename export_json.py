#!/usr/bin/env python3
"""Export the quotations database to JSON."""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "quotations.db"
JSON_PATH = ROOT / "quotations.json"


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run 'python run_all.py' first to build it.")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT scripture_reference, quoted_from, source FROM quotation ORDER BY id"
    ).fetchall()
    conn.close()

    data = [
        {
            "scripture_reference": row["scripture_reference"],
            "quoted_from": row["quoted_from"],
            "source": row["source"],
        }
        for row in rows
    ]

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Exported {len(data)} records to {JSON_PATH.name}")


if __name__ == "__main__":
    main()
