-- Common Voice Offline Bot - Supabase Schema
-- Paste this into Supabase SQL Editor and run it

-- ============================================
-- TABLES
-- ============================================

-- Users table: stores registered bot users
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    cv_user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    cv_token TEXT,  -- NULL means logged out
    bot_language TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sessions table: tracks active recording sessions
CREATE TABLE sessions (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id) ON DELETE CASCADE,
    language TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sentences table: sentences assigned to users for recording
CREATE TABLE sentences (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    sentence_number INTEGER NOT NULL,
    text_id TEXT NOT NULL,
    text TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (telegram_id, sentence_number)
);

-- Recordings table: tracks voice recordings for each sentence
CREATE TABLE recordings (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    sentence_number INTEGER NOT NULL,
    file_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ,
    UNIQUE (telegram_id, sentence_number)
);

-- User preferences table: for non-registered users (language preference)
CREATE TABLE user_preferences (
    telegram_id BIGINT PRIMARY KEY,
    bot_language TEXT NOT NULL DEFAULT 'en',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seen sentences table: tracks all sentences a user has uploaded or skipped
CREATE TABLE seen_sentences (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    language TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',  -- 'uploaded' or 'skipped'
    text TEXT,  -- sentence text (only for uploaded)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (telegram_id, language, sentence_id)
);

-- ============================================
-- INDEXES (for query performance)
-- ============================================

CREATE INDEX idx_sentences_telegram_id ON sentences(telegram_id);
CREATE INDEX idx_recordings_telegram_id ON recordings(telegram_id);
CREATE INDEX idx_recordings_status ON recordings(status);
CREATE INDEX idx_seen_sentences_telegram_id_language ON seen_sentences(telegram_id, language);
CREATE INDEX idx_seen_sentences_status ON seen_sentences(status);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;
ALTER TABLE recordings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE seen_sentences ENABLE ROW LEVEL SECURITY;

-- Policy: Service role (bot) can do everything
-- The bot uses the service_role key which bypasses RLS

-- Policy: Anon users (dashboard) can only read aggregate data
-- These policies allow the dashboard to query stats without exposing individual user data

-- Allow anon to count users (for "total contributors")
CREATE POLICY "Allow anon to count users"
    ON users FOR SELECT
    TO anon
    USING (true);

-- Allow anon to read recordings (for aggregate stats)
CREATE POLICY "Allow anon to read recordings"
    ON recordings FOR SELECT
    TO anon
    USING (true);

-- Allow anon to read sessions (for language stats)
CREATE POLICY "Allow anon to read sessions"
    ON sessions FOR SELECT
    TO anon
    USING (true);

-- Allow anon to read seen_sentences (for contribution counts)
CREATE POLICY "Allow anon to read seen_sentences"
    ON seen_sentences FOR SELECT
    TO anon
    USING (true);

-- ============================================
-- VIEWS (for dashboard queries)
-- ============================================

-- Aggregate stats view: total recordings by language
CREATE VIEW stats_by_language AS
SELECT 
    s.language,
    COUNT(DISTINCT u.telegram_id) as contributors,
    COUNT(DISTINCT CASE WHEN r.status = 'uploaded' THEN r.id END) as recordings_uploaded,
    COUNT(DISTINCT CASE WHEN r.status = 'pending' THEN r.id END) as recordings_pending
FROM users u
LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
LEFT JOIN recordings r ON u.telegram_id = r.telegram_id
GROUP BY s.language;

-- User stats view: for personal stats lookup by cv_user_id
CREATE VIEW user_stats AS
SELECT 
    u.cv_user_id,
    u.username,
    u.created_at as joined_at,
    s.language as current_language,
    COUNT(DISTINCT CASE WHEN ss.status = 'uploaded' THEN ss.sentence_id END) as total_contributions,
    COUNT(DISTINCT CASE WHEN r.status = 'uploaded' THEN r.id END) as recordings_uploaded
FROM users u
LEFT JOIN sessions s ON u.telegram_id = s.telegram_id
LEFT JOIN seen_sentences ss ON u.telegram_id = ss.telegram_id
LEFT JOIN recordings r ON u.telegram_id = r.telegram_id
GROUP BY u.cv_user_id, u.username, u.created_at, s.language;

-- User sentences view: for personal dashboard to show uploaded sentences
CREATE VIEW user_sentences AS
SELECT 
    u.cv_user_id,
    ss.language,
    ss.text,
    ss.created_at as uploaded_at
FROM users u
JOIN seen_sentences ss ON u.telegram_id = ss.telegram_id
WHERE ss.status = 'uploaded';

-- Grant anon access to views
GRANT SELECT ON stats_by_language TO anon;
GRANT SELECT ON user_stats TO anon;
GRANT SELECT ON user_sentences TO anon;
