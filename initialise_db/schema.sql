-- Schema for Bible Quotation Database
-- Stores places where the Bible quotes itself,
-- especially the New Testament quoting the Old Testament.

CREATE TABLE IF NOT EXISTS quotation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scripture_reference TEXT NOT NULL,  -- The verse that contains the quotation (e.g. NT verse)
    quoted_from TEXT NOT NULL,          -- The verse being quoted (e.g. OT verse)
    source TEXT NOT NULL,               -- Which data source this came from
    UNIQUE(scripture_reference, quoted_from, source)
);

CREATE INDEX IF NOT EXISTS idx_quotation_scripture ON quotation(scripture_reference);
CREATE INDEX IF NOT EXISTS idx_quotation_quoted_from ON quotation(quoted_from);
