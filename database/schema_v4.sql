-- CareCircle — Sprint 1 Migration v4
-- Run in Supabase SQL Editor (safe to re-run)

-- ==========================================
-- 1. active_patient_id in user_profiles
--    Tracks which patient is "active" for bot + future multi-patient scenarios
-- ==========================================
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS active_patient_id UUID REFERENCES patients(id);

-- ==========================================
-- 2. share_links table
--    Public read-only 7-day links for sharing a patient summary
-- ==========================================
CREATE TABLE IF NOT EXISTS share_links (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id   UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    token        VARCHAR(64) UNIQUE NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_share_links_token ON share_links(token);

ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "backend_full_access" ON share_links;
CREATE POLICY "backend_full_access" ON share_links
    FOR ALL TO service_role USING (true) WITH CHECK (true);
