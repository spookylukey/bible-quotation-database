# Bible Quotation Database

A database of places where the Bible quotes itself, especially the New
Testament quoting the Old Testament.

## Download

If you just want the data, download **`quotations.db`** from the
[releases page](https://github.com/spookylukey/bible-quotation-database/releases).
It is a SQLite database you can query directly — no build step required.

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
python initialise_db/create_db.py                # Create/recreate empty DB
python populate_db/source_bible_researcher.py     # Source 1
python populate_db/source_kalvesmaki.py           # Source 2
```

## Sources

- [bible-researcher.com](https://www.bible-researcher.com/quote02.html) — ~719 quotation pairs
- [kalvesmaki.com](https://www.kalvesmaki.com/LXX/NTChart.htm) — ~623 quotation pairs

## Schema

See `initialise_db/schema.sql`. The `quotation` table stores:

| Column                 | Description                                                             |
| ---------------------- | ----------------------------------------------------------------------- |
| `scripture_reference`  | The verse containing the quotation (e.g. `Romans 1:23`)                 |
| `quoted_from`          | The verse being quoted (e.g. `Genesis 1:26`)                            |
| `source`               | Which data source the record came from                                  |

All multi-verse ranges are expanded to individual verse references.
