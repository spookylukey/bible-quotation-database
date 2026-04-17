#!/usr/bin/env python3
"""Export the quotations database to CSV."""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "quotations.db"
CSV_PATH = ROOT / "quotations.csv"


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run 'python run_all.py' first to build it.")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT scripture_reference, quoted_from, source FROM quotation ORDER BY id"
    ).fetchall()
    conn.close()

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scripture_reference", "quoted_from", "source"])
        writer.writerows(rows)

    print(f"Exported {len(rows)} records to {CSV_PATH.name}")


if __name__ == "__main__":
    main()
