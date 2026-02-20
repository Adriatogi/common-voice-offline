-- Common Voice Offline Bot - Supabase Schema
-- Paste this into Supabase SQL Editor and run it

-- ============================================
-- TABLES
-- ============================================

-- Users table: maps telegram users to their current CV account
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    cv_user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    cv_token TEXT,  -- NULL means logged out
    current_language TEXT,  -- Current recording language (set by /setup)
    bot_language TEXT NOT NULL DEFAULT 'es',
    age TEXT,  -- Age range for CV uploads (e.g., 'twenties', 'thirties')
    gender TEXT,  -- Gender for CV uploads (e.g., 'male_masculine', 'female_feminine')
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sentences table: all sentences ever assigned (merged with seen_sentences)
CREATE TABLE sentences (
    id BIGSERIAL PRIMARY KEY,
    cv_user_id TEXT NOT NULL,
    language TEXT NOT NULL,
    sentence_number INTEGER NOT NULL,  -- 1, 2, 3... within current batch
    text_id TEXT NOT NULL,  -- Common Voice sentence ID
    text TEXT NOT NULL,
    hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'uploaded', 'skipped'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Recordings table: tracks voice recordings for each sentence
CREATE TABLE recordings (
    id BIGSERIAL PRIMARY KEY,
    sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    file_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'uploaded', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ,
    UNIQUE (sentence_id)
);

-- User preferences table: for non-registered users (bot language preference)
CREATE TABLE user_preferences (
    telegram_id BIGINT PRIMARY KEY,
    bot_language TEXT NOT NULL DEFAULT 'es',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_sentences_cv_user_id ON sentences(cv_user_id);
CREATE INDEX idx_sentences_cv_user_language ON sentences(cv_user_id, language);
CREATE INDEX idx_sentences_status ON sentences(status);
CREATE INDEX idx_recordings_sentence_id ON recordings(sentence_id);
CREATE INDEX idx_recordings_status ON recordings(status);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;
ALTER TABLE recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Anon can read for dashboard
CREATE POLICY "Allow anon to read users" ON users FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon to read sentences" ON sentences FOR SELECT TO anon USING (true);
CREATE POLICY "Allow anon to read recordings" ON recordings FOR SELECT TO anon USING (true);

-- ============================================
-- VIEWS (for dashboard)
-- ============================================

-- Aggregate stats by language
CREATE VIEW stats_by_language AS
SELECT 
    language,
    COUNT(DISTINCT cv_user_id) as contributors,
    COUNT(*) FILTER (WHERE status = 'uploaded') as recordings_uploaded,
    COUNT(*) FILTER (WHERE status = 'active') as recordings_pending
FROM sentences
GROUP BY language;

-- User stats for personal dashboard
CREATE VIEW user_stats AS
SELECT 
    cv_user_id,
    COUNT(*) FILTER (WHERE status = 'uploaded') as total_contributions,
    COUNT(DISTINCT language) FILTER (WHERE status = 'uploaded') as languages_contributed
FROM sentences
GROUP BY cv_user_id;

-- User sentences for personal dashboard (uploaded only)
CREATE VIEW user_sentences AS
SELECT 
    cv_user_id,
    language,
    text,
    created_at as uploaded_at
FROM sentences
WHERE status = 'uploaded';

-- Grant anon access to views
GRANT SELECT ON stats_by_language TO anon;
GRANT SELECT ON user_stats TO anon;
GRANT SELECT ON user_sentences TO anon;
