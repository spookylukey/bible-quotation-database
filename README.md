# Bible Quotation Database

A database of places where the Bible quotes itself, especially the New
Testament quoting the Old Testament.

## Download

If you just want the data, download from [source directory](https://github.com/spookylukey/bible-quotation-database):

- [quotations.db](https://raw.githubusercontent.com/spookylukey/bible-quotation-database/refs/heads/main/quotations.db) — SQLite database you can query directly
- [quotations_single.csv](https://raw.githubusercontent.com/spookylukey/bible-quotation-database/refs/heads/main/quotations_single.csv) — CSV export, single-verse normalised
- [quotations_range.csv](https://raw.githubusercontent.com/spookylukey/bible-quotation-database/refs/heads/main/quotations_range.csv) — CSV export, verse ranges preserved
- [quotations_single.json](https://raw.githubusercontent.com/spookylukey/bible-quotation-database/refs/heads/main/quotations_single.json) — JSON, single-verse normalised
- [quotations_range.json](https://raw.githubusercontent.com/spookylukey/bible-quotation-database/refs/heads/main/quotations_range.json) — JSON, verse ranges preserved

No build step required.

See [Schema](#schema) below for the table structure.

---

Everything below is only needed if you want to **rebuild the database
from source data**.

## Setup

```bash
uv venv
uv pip install -e .
```

## Rebuilding the database

Run everything (create DB + populate from all sources):

```bash
source .venv/bin/activate
python run_all.py
```

Or run individual steps:

```bash
python initialise_db/create_db.py                 # Create/recreate empty DB
python populate_db/source_bible_researcher.py     # Source 1
python populate_db/source_kalvesmaki.py           # Source 2
python export_db/export_csv.py                    # Export to CSV
python export_db/export_json.py                   # Export to JSON
python export_db/export_web_json.py               # Export web app JSON
```

## Sources

- [bible-researcher.com](https://www.bible-researcher.com/quote02.html) — ~719 quotation pairs
- [kalvesmaki.com](https://www.kalvesmaki.com/LXX/NTChart.htm) — ~327 quotation pairs (range), ~623 (single)

## Schema

See `initialise_db/schema.sql`. The database has two tables:

### `quotation_single`

All multi-verse ranges are expanded to individual verse references.

| Column                 | Description                                                             |
| ---------------------- | ----------------------------------------------------------------------- |
| `scripture_reference`  | The verse containing the quotation (e.g. `Romans 1:23`)                 |
| `quoted_from`          | The verse being quoted (e.g. `Genesis 1:26`)                            |
| `source`               | Which data source the record came from                                  |

### `quotation_range`

Verse ranges are preserved as-is from the source data.

| Column                 | Description                                                             |
| ---------------------- | ----------------------------------------------------------------------- |
| `scripture_reference`  | The verse or range containing the quotation (e.g. `Matthew 12:18-21`)   |
| `quoted_from`          | The verse or range being quoted (e.g. `Isaiah 42:1-4`)                  |
| `source`               | Which data source the record came from                                  |
