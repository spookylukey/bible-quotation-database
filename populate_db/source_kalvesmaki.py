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

from populate_db.ref_utils import (
    normalise_reference_from_start,
    range_reference_from_start,
    parse_reference_from_start,
)
from populate_db.db_utils import get_connection, insert_quotation_single, insert_quotation_range

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
    parts = re.split(r"<br\s*/??>\s*(?:<br\s*/??>\s*)*", raw_html)

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


def parse_and_insert(html: str) -> tuple[int, int, int, list[str]]:
    """Parse the HTML and insert records.

    Returns (rows_processed, single_inserted, range_inserted, errors).
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        raise ValueError("Could not find table")

    rows = table.find_all("tr")

    conn = get_connection()
    # Clear previous data from this source
    conn.execute("DELETE FROM quotation_single WHERE source = ?", (SOURCE_NAME,))
    conn.execute("DELETE FROM quotation_range WHERE source = ?", (SOURCE_NAME,))

    rows_processed = 0
    single_inserted = 0
    range_inserted = 0
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

        # Parse single-verse (expanded) refs
        nt_single_all = []
        nt_range_all = []
        for block in nt_blocks:
            try:
                nt_single_all.extend(normalise_reference_from_start(block))
                nt_range_all.append(range_reference_from_start(block))
            except Exception as e:
                errors.append(f"Row {row_idx} NT: failed to parse '{block[:80]}': {e}")

        ot_single_all = []
        ot_range_all = []
        for block in ot_blocks:
            try:
                ot_single_all.extend(normalise_reference_from_start(block))
                ot_range_all.append(range_reference_from_start(block))
            except Exception as e:
                errors.append(f"Row {row_idx} OT: failed to parse '{block[:80]}': {e}")

        if not nt_single_all or not ot_single_all:
            if not nt_single_all:
                errors.append(f"Row {row_idx}: no NT refs extracted from {[b[:60] for b in nt_blocks]}")
            if not ot_single_all:
                errors.append(f"Row {row_idx}: no OT refs extracted from {[b[:60] for b in ot_blocks]}")
            continue

        # Insert single-verse (expanded) records
        for sr in nt_single_all:
            for qf in ot_single_all:
                insert_quotation_single(conn, sr, qf, SOURCE_NAME)
                single_inserted += 1

        # Insert range records
        for sr in nt_range_all:
            for qf in ot_range_all:
                insert_quotation_range(conn, sr, qf, SOURCE_NAME)
                range_inserted += 1

    conn.commit()
    conn.close()
    return rows_processed, single_inserted, range_inserted, errors


def self_test(rows_processed: int, single_inserted: int, range_inserted: int, errors: list[str]):
    """Basic sanity checks."""
    assert rows_processed >= 185, f"Expected >=185 rows, got {rows_processed}"
    assert single_inserted > 200, f"Expected >200 single records, got {single_inserted}"
    assert range_inserted > 200, f"Expected >200 range records, got {range_inserted}"
    error_rate = len(errors) / rows_processed if rows_processed else 1
    assert error_rate < 0.10, f"Error rate too high: {error_rate:.1%} ({len(errors)}/{rows_processed})"

    # Verify DB contents
    conn = get_connection()
    count_single = conn.execute("SELECT COUNT(*) FROM quotation_single WHERE source = ?", (SOURCE_NAME,)).fetchone()[0]
    count_range = conn.execute("SELECT COUNT(*) FROM quotation_range WHERE source = ?", (SOURCE_NAME,)).fetchone()[0]
    conn.close()
    assert count_single > 200, f"Expected >200 single DB records, got {count_single}"
    assert count_range > 200, f"Expected >200 range DB records, got {count_range}"
    print(f"Self-test passed: {count_single} single records, {count_range} range records in DB from {SOURCE_NAME}")


def main():
    print(f"Fetching {SOURCE_URL} ...")
    html = fetch_page()
    print(f"Parsing and inserting ...")
    rows_processed, single_inserted, range_inserted, errors = parse_and_insert(html)

    print(f"Rows processed: {rows_processed}")
    print(f"Single records inserted: {single_inserted}")
    print(f"Range records inserted: {range_inserted}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  {e}")

    self_test(rows_processed, single_inserted, range_inserted, errors)


if __name__ == "__main__":
    main()
