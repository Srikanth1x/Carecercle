-- CareCircle — Production Migration v3
-- Run this in Supabase SQL Editor.
-- Safe to re-run (uses IF NOT EXISTS / IF EXISTS / OR REPLACE).

-- ==========================================
-- 1. Apply schema_v2 (user_id on patients)
-- ==========================================
ALTER TABLE patients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    telegram_chat_id VARCHAR(50) UNIQUE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- 2. Missing column: acknowledged_at on alerts
-- ==========================================
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMPTZ;

-- ==========================================
-- 3. Fix RLS policies
--    Old "service_role_all" used USING (true) with no role binding,
--    granting full access to anon and authenticated users.
--    Replace with policies explicitly bound to the service_role.
-- ==========================================
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN VALUES
        ('patients'),('medications'),('lab_reports'),('care_events'),
        ('alerts'),('consent_log'),('appointments'),('daily_briefings'),
        ('doctors'),('user_profiles')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS "service_role_all" ON %I', t);
        EXECUTE format('DROP POLICY IF EXISTS "backend_full_access" ON %I', t);
        EXECUTE format(
            'CREATE POLICY "backend_full_access" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)',
            t
        );
    END LOOP;
END $$;

-- ==========================================
-- 4. Missing indexes
-- ==========================================

-- lab_reports: date-range queries by patient
CREATE INDEX IF NOT EXISTS idx_lab_reports_patient_date
    ON lab_reports(patient_id, test_date DESC);

-- appointments: upcoming scheduled appointments per patient
CREATE INDEX IF NOT EXISTS idx_appointments_patient_date_status
    ON appointments(patient_id, appointment_date)
    WHERE status = 'scheduled';

-- consent_log: time-bounded queries per patient
CREATE INDEX IF NOT EXISTS idx_consent_log_patient_created
    ON consent_log(patient_id, created_at DESC);

-- ==========================================
-- 5. CHECK constraints on status columns
--    Prevents silent typos that break filter queries
-- ==========================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_medications_status'
    ) THEN
        ALTER TABLE medications ADD CONSTRAINT chk_medications_status
            CHECK (status IN ('active', 'superseded', 'discontinued', 'on_hold', 'completed'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_alerts_status'
    ) THEN
        ALTER TABLE alerts ADD CONSTRAINT chk_alerts_status
            CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'chk_appointments_status'
    ) THEN
        ALTER TABLE appointments ADD CONSTRAINT chk_appointments_status
            CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show'));
    END IF;
END $$;

-- ==========================================
-- 6. Unique constraint: one briefing per patient per day
-- ==========================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'uq_daily_briefings_patient_date'
    ) THEN
        ALTER TABLE daily_briefings
            ADD CONSTRAINT uq_daily_briefings_patient_date
            UNIQUE (patient_id, briefing_date);
    END IF;
END $$;

-- ==========================================
-- 7. updated_at triggers for patients and medications
-- ==========================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_patients_updated_at ON patients;
CREATE TRIGGER trg_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_medications_updated_at ON medications;
CREATE TRIGGER trg_medications_updated_at
    BEFORE UPDATE ON medications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ==========================================
-- 8. Unique index on doctors.hpr_id (nationally unique ID)
-- ==========================================
DROP INDEX IF EXISTS uq_doctors_hpr_id_notnull;
CREATE UNIQUE INDEX uq_doctors_hpr_id_notnull
    ON doctors(hpr_id)
    WHERE hpr_id IS NOT NULL;

-- ==========================================
-- 9. Link seed patient to your auth user
--    Replace <YOUR_AUTH_USER_UUID> with your actual UUID from:
--    Supabase dashboard → Authentication → Users → copy the user ID
-- ==========================================
-- UPDATE patients
-- SET user_id = '<YOUR_AUTH_USER_UUID>'
-- WHERE id = 'e6e4be6c-2676-490b-8a96-ec1e8c7500d9';

-- Also create the user_profile row so Telegram linking works:
-- INSERT INTO user_profiles (user_id)
-- VALUES ('<YOUR_AUTH_USER_UUID>')
-- ON CONFLICT DO NOTHING;
