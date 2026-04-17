#!/usr/bin/env python3
"""Populate DB from https://www.bible-researcher.com/quote02.html

This page has two tables (OT order and NT order) with the same data.
We use the first table (OT order). Each row has two cells:
  cell 0 = OT reference (quoted_from)
  cell 1 = NT reference (scripture_reference)
"""

import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from populate_db.ref_utils import normalise_reference
from populate_db.db_utils import get_connection, insert_quotation

SOURCE_URL = "https://www.bible-researcher.com/quote02.html"
SOURCE_NAME = "bible-researcher.com"


def fetch_page() -> str:
    r = requests.get(SOURCE_URL, timeout=30)
    r.raise_for_status()
    return r.text


def parse_and_insert(html: str) -> tuple[int, int, list[str]]:
    """Parse the HTML and insert records.

    Returns (rows_processed, records_inserted, errors).
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_="quote")
    if len(tables) < 1:
        raise ValueError("Could not find quote tables")

    # Use first table (OT order): cell0=OT, cell1=NT
    table = tables[0]
    rows = table.find_all("tr")

    conn = get_connection()
    # Clear previous data from this source
    conn.execute("DELETE FROM quotation WHERE source = ?", (SOURCE_NAME,))

    rows_processed = 0
    records_inserted = 0
    errors = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        # Skip header row
        if cells[0].get("class") and "head" in cells[0].get("class", []):
            continue

        ot_text = cells[0].get_text(strip=True)
        nt_text = cells[1].get_text(strip=True)

        if not ot_text or not nt_text:
            continue

        rows_processed += 1

        try:
            ot_refs = normalise_reference(ot_text)
            nt_refs = normalise_reference(nt_text)
        except Exception as e:
            errors.append(f"Row {rows_processed}: failed to parse '{ot_text}' / '{nt_text}': {e}")
            continue

        for sr in nt_refs:
            for qf in ot_refs:
                insert_quotation(conn, sr, qf, SOURCE_NAME)
                records_inserted += 1

    conn.commit()
    conn.close()
    return rows_processed, records_inserted, errors


def self_test(rows_processed: int, records_inserted: int, errors: list[str]):
    """Basic sanity checks."""
    assert rows_processed > 600, f"Expected >600 rows, got {rows_processed}"
    assert records_inserted > 600, f"Expected >600 records, got {records_inserted}"
    error_rate = len(errors) / rows_processed if rows_processed else 1
    assert error_rate < 0.05, f"Error rate too high: {error_rate:.1%} ({len(errors)}/{rows_processed})"

    # Verify DB contents
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM quotation WHERE source = ?", (SOURCE_NAME,)).fetchone()[0]
    conn.close()
    assert count > 600, f"Expected >600 DB records, got {count}"
    print(f"Self-test passed: {count} records in DB from {SOURCE_NAME}")


def main():
    print(f"Fetching {SOURCE_URL} ...")
    html = fetch_page()
    print(f"Parsing and inserting ...")
    rows_processed, records_inserted, errors = parse_and_insert(html)

    print(f"Rows processed: {rows_processed}")
    print(f"Records inserted: {records_inserted}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")

    self_test(rows_processed, records_inserted, errors)


if __name__ == "__main__":
    main()
