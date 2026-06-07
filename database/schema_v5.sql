-- Aayu — Sprint 2 Migration v5
-- Run in Supabase SQL Editor (safe to re-run)

-- ==========================================
-- 1. ABHA verification status on patients
-- ==========================================
ALTER TABLE patients ADD COLUMN IF NOT EXISTS abha_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS abha_verified_at TIMESTAMPTZ;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS abha_mobile_last4 TEXT;

-- ==========================================
-- 2. ABDM sandbox credentials (per user)
--    Stores the linked ABHA number after OTP verification
-- ==========================================
CREATE TABLE IF NOT EXISTS abha_verifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    abha_number     TEXT NOT NULL,
    abha_address    TEXT,
    name_on_abha    TEXT,
    gender          TEXT,
    year_of_birth   TEXT,
    mobile_last4    TEXT,
    verified_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_response    JSONB,
    UNIQUE(patient_id)
);

-- RLS: service_role full access
ALTER TABLE abha_verifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS backend_full_access ON abha_verifications;
CREATE POLICY backend_full_access ON abha_verifications TO service_role USING (true) WITH CHECK (true);
