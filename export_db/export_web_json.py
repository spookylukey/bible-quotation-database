#!/usr/bin/env python3
"""Export quotations from SQLite to a de-duplicated JSON file for the web app.

Uses the quotation_range table so that verse ranges are preserved.
Deduplicates by removing single-verse pairs that are fully covered by
a range pair (e.g. if we have Matthew 12:18-21 → Isaiah 42:1-4, we
remove Matthew 12:19 → Isaiah 42:2 etc.).
"""

import json
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "quotations.db"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "web" / "quotations.json"


def parse_ref(ref: str):
    """Parse 'Book Chapter:Verse' or 'Book Chapter:Start-End' into (book, chapter, start, end)."""
    m = re.match(r'^(.+?)\s+(\d+):(\d+)(?:-(\d+))?$', ref)
    if not m:
        return None
    book = m.group(1)
    chapter = int(m.group(2))
    start = int(m.group(3))
    end = int(m.group(4)) if m.group(4) else start
    return (book, chapter, start, end)


def is_subsumed(single_ref: str, range_ref: str) -> bool:
    """Check if single_ref is a single verse contained within range_ref."""
    s = parse_ref(single_ref)
    r = parse_ref(range_ref)
    if not s or not r:
        return False
    return (s[0] == r[0] and s[1] == r[1] and
            r[2] <= s[2] <= r[3] and s[3] == s[2])  # single verse within range


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT DISTINCT scripture_reference, quoted_from FROM quotation_range"
    )
    rows = cursor.fetchall()
    conn.close()

    records = [{"nt": nt, "ot": ot} for nt, ot in rows]

    # Identify range records (where either ref has a dash = multi-verse)
    range_records = [r for r in records if '-' in r['nt'] or '-' in r['ot']]

    # Build a set of single-verse pairs that are subsumed by a range pair
    subsumed = set()
    for rr in range_records:
        for rec in records:
            if rec is rr:
                continue
            nt_sub = (rec['nt'] == rr['nt']) or is_subsumed(rec['nt'], rr['nt'])
            ot_sub = (rec['ot'] == rr['ot']) or is_subsumed(rec['ot'], rr['ot'])
            if nt_sub and ot_sub:
                subsumed.add((rec['nt'], rec['ot']))

    # Filter out subsumed records
    filtered = [r for r in records if (r['nt'], r['ot']) not in subsumed]
    removed = len(records) - len(filtered)

    filtered.sort(key=lambda r: r["ot"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(filtered)} unique quotations to {OUTPUT_PATH} ({removed} subsumed records removed)")


if __name__ == "__main__":
    main()
