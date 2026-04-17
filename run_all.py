#!/usr/bin/env python3
"""Master script: recreate DB from scratch and populate from all sources."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

steps = [
    ("Initialise DB", [sys.executable, str(ROOT / "initialise_db" / "create_db.py")]),
    ("Populate from bible-researcher.com", [sys.executable, str(ROOT / "populate_db" / "source_bible_researcher.py")]),
    ("Populate from kalvesmaki.com", [sys.executable, str(ROOT / "populate_db" / "source_kalvesmaki.py")]),
    ("Export CSV", [sys.executable, str(ROOT / "export_csv.py")]),
    ("Export JSON", [sys.executable, str(ROOT / "export_json.py")]),
]


def main():
    for desc, cmd in steps:
        print(f"\n{'='*60}")
        print(f"  {desc}")
        print(f"{'='*60}")
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            print(f"FAILED: {desc}")
            sys.exit(1)

    print(f"\n{'='*60}")
    print("  All done!")
    print(f"{'='*60}")

    # Summary
    import sqlite3
    conn = sqlite3.connect(ROOT / "quotations.db")
    total = conn.execute("SELECT COUNT(*) FROM quotation").fetchone()[0]
    by_source = conn.execute("SELECT source, COUNT(*) FROM quotation GROUP BY source").fetchall()
    conn.close()
    print(f"\nTotal records: {total}")
    for source, count in by_source:
        print(f"  {source}: {count}")


if __name__ == "__main__":
    main()
