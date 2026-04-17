#!/usr/bin/env python3
"""Export the quotations database to CSV files."""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "quotations.db"


def export_table(db_path: Path, table: str, output_path: Path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        f"SELECT scripture_reference, quoted_from, source FROM {table} ORDER BY id"
    ).fetchall()
    conn.close()

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scripture_reference", "quoted_from", "source"])
        writer.writerows(rows)

    print(f"Exported {len(rows)} records to {output_path.name}")


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run 'python run_all.py' first to build it.")
        raise SystemExit(1)

    export_table(DB_PATH, "quotation_single", ROOT / "quotations_single.csv")
    export_table(DB_PATH, "quotation_range", ROOT / "quotations_range.csv")


if __name__ == "__main__":
    main()
