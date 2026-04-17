#!/usr/bin/env python3
"""Export quotations from SQLite to a de-duplicated JSON file for the web app."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "quotations.db"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "web" / "quotations.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT DISTINCT scripture_reference, quoted_from FROM quotation"
    )
    rows = cursor.fetchall()
    conn.close()

    records = [{"nt": nt, "ot": ot} for nt, ot in rows]
    records.sort(key=lambda r: r["ot"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(records)} unique quotations to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
