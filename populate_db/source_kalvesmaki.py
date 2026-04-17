#!/usr/bin/env python3
"""Populate DB from https://www.kalvesmaki.com/LXX/NTChart.htm

This page has one table with 3 columns:
  cell 0 = NT quotation text (may contain multiple NT refs, separated by <p> or <br>)
  cell 1 = LXX (Septuagint) text - we skip this
  cell 2 = Masoretic (OT) text with reference

Each cell starts with a Bible reference followed by the quotation text.
We extract the reference from the start of each text block.
"""

import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from populate_db.ref_utils import normalise_reference_from_start, expand_to_single_verses, parse_reference_from_start
from populate_db.db_utils import get_connection, insert_quotation

SOURCE_URL = "https://www.kalvesmaki.com/LXX/NTChart.htm"
SOURCE_NAME = "kalvesmaki.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_page() -> str:
    r = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def extract_text_blocks(cell: Tag) -> list[str]:
    """Extract individual text blocks from a cell.

    Cells may contain multiple references separated by <p> tags or <br> tags.
    """
    # Check for <p> tags first
    ps = cell.find_all("p")
    if len(ps) > 1:
        return [p.get_text(strip=True) for p in ps if p.get_text(strip=True)]

    # Check for <br> tags — split on them
    # Get the full text and split on patterns that look like a new reference after a period/text
    fonts = cell.find_all("font")
    if fonts:
        # Get inner HTML of font tag(s), split on <br/> or <br>
        raw_html = "".join(str(f) for f in fonts)
    else:
        raw_html = str(cell)

    # Split on <br/> or <br> tags
    parts = re.split(r"<br\s*/?>\s*(?:<br\s*/?>\s*)*", raw_html)

    results = []
    for part in parts:
        # Strip HTML tags to get text
        text = BeautifulSoup(part, "lxml").get_text(strip=True)
        if text:
            results.append(text)

    # If we only got one block, return it
    if len(results) <= 1:
        return results

    # For <br>-separated blocks, the second block might not start with a book name.
    # Merge blocks that don't start with a recognizable reference.
    merged = []
    for text in results:
        try:
            parse_reference_from_start(text)
            merged.append(text)
        except Exception:
            # Doesn't start with a reference — append to previous block
            if merged:
                merged[-1] += " " + text
            else:
                merged.append(text)
    return merged


def parse_and_insert(html: str) -> tuple[int, int, list[str]]:
    """Parse the HTML and insert records.

    Returns (rows_processed, records_inserted, errors).
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        raise ValueError("Could not find table")

    rows = table.find_all("tr")

    conn = get_connection()
    # Clear previous data from this source
    conn.execute("DELETE FROM quotation WHERE source = ?", (SOURCE_NAME,))

    rows_processed = 0
    records_inserted = 0
    errors = []

    for row_idx, row in enumerate(rows[1:], start=1):  # Skip header
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        rows_processed += 1

        # Extract NT references (cell 0)
        nt_blocks = extract_text_blocks(cells[0])
        # Extract OT references (cell 2 = Masoretic)
        ot_blocks = extract_text_blocks(cells[2])

        nt_refs_all = []
        for block in nt_blocks:
            try:
                refs = normalise_reference_from_start(block)
                nt_refs_all.extend(refs)
            except Exception as e:
                errors.append(f"Row {row_idx} NT: failed to parse '{block[:80]}': {e}")

        ot_refs_all = []
        for block in ot_blocks:
            try:
                refs = normalise_reference_from_start(block)
                ot_refs_all.extend(refs)
            except Exception as e:
                errors.append(f"Row {row_idx} OT: failed to parse '{block[:80]}': {e}")

        if not nt_refs_all or not ot_refs_all:
            if not nt_refs_all:
                errors.append(f"Row {row_idx}: no NT refs extracted from {[b[:60] for b in nt_blocks]}")
            if not ot_refs_all:
                errors.append(f"Row {row_idx}: no OT refs extracted from {[b[:60] for b in ot_blocks]}")
            continue

        for sr in nt_refs_all:
            for qf in ot_refs_all:
                insert_quotation(conn, sr, qf, SOURCE_NAME)
                records_inserted += 1

    conn.commit()
    conn.close()
    return rows_processed, records_inserted, errors


def self_test(rows_processed: int, records_inserted: int, errors: list[str]):
    """Basic sanity checks."""
    assert rows_processed >= 185, f"Expected >=185 rows, got {rows_processed}"
    assert records_inserted > 200, f"Expected >200 records, got {records_inserted}"
    error_rate = len(errors) / rows_processed if rows_processed else 1
    assert error_rate < 0.10, f"Error rate too high: {error_rate:.1%} ({len(errors)}/{rows_processed})"

    # Verify DB contents
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM quotation WHERE source = ?", (SOURCE_NAME,)).fetchone()[0]
    conn.close()
    assert count > 200, f"Expected >200 DB records, got {count}"
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
