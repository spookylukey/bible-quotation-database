-- Schema for Bible Quotation Database
-- Stores places where the Bible quotes itself,
-- especially the New Testament quoting the Old Testament.

-- Single-verse normalised references (every range expanded to individual verses)
CREATE TABLE IF NOT EXISTS quotation_single (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scripture_reference TEXT NOT NULL,  -- The verse that contains the quotation (e.g. NT verse)
    quoted_from TEXT NOT NULL,          -- The verse being quoted (e.g. OT verse)
    source TEXT NOT NULL,               -- Which data source this came from
    UNIQUE(scripture_reference, quoted_from, source)
);

CREATE INDEX IF NOT EXISTS idx_qs_scripture ON quotation_single(scripture_reference);
CREATE INDEX IF NOT EXISTS idx_qs_quoted_from ON quotation_single(quoted_from);

-- Range references (not normalised — may be single verses or verse ranges)
CREATE TABLE IF NOT EXISTS quotation_range (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scripture_reference TEXT NOT NULL,  -- The verse/range containing the quotation (e.g. "Matthew 12:18-21")
    quoted_from TEXT NOT NULL,          -- The verse/range being quoted (e.g. "Isaiah 42:1-4")
    source TEXT NOT NULL,               -- Which data source this came from
    UNIQUE(scripture_reference, quoted_from, source)
);

CREATE INDEX IF NOT EXISTS idx_qr_scripture ON quotation_range(scripture_reference);
CREATE INDEX IF NOT EXISTS idx_qr_quoted_from ON quotation_range(quoted_from);
