#!/usr/bin/env python3
"""Export the quotations database to JSON files."""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "quotations.db"


def export_table(db_path: Path, table: str, output_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT scripture_reference, quoted_from, source FROM {table} ORDER BY id"
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

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Exported {len(data)} records to {output_path.name}")


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run 'python run_all.py' first to build it.")
        raise SystemExit(1)

    export_table(DB_PATH, "quotation_single", ROOT / "quotations_single.json")
    export_table(DB_PATH, "quotation_range", ROOT / "quotations_range.json")


if __name__ == "__main__":
    main()
