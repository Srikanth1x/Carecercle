-- CareCircle MVP — Supabase Schema
-- Paste this entire file into the Supabase SQL Editor and run it.

-- ==========================================
-- TABLE: patients
-- ABDM Concept: ABHA Registry Entry
-- ==========================================
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    abha_id VARCHAR(14) UNIQUE NOT NULL,
    abha_address VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    blood_group VARCHAR(10),
    phone VARCHAR(15),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(15),
    address_city VARCHAR(100),
    address_state VARCHAR(100),
    known_conditions TEXT[],
    primary_caregiver_telegram_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: doctors
-- ABDM Concept: Healthcare Professional Registry (HPR)
-- ==========================================
CREATE TABLE IF NOT EXISTS doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    specialty VARCHAR(100),
    hospital VARCHAR(200),
    phone VARCHAR(15),
    emergency_phone VARCHAR(15),
    hpr_id VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: medications
-- ABDM Concept: Prescription Record (versioned)
-- ==========================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    doctor_id UUID REFERENCES doctors(id),
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    timing VARCHAR(100),
    route VARCHAR(50) DEFAULT 'oral',
    purpose VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active',
    superseded_by UUID REFERENCES medications(id),
    version INTEGER DEFAULT 1,
    prescribed_date DATE,
    end_date DATE,
    source_type VARCHAR(50),
    source_raw_text TEXT,
    abdm_record_type VARCHAR(50) DEFAULT 'Prescription',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: lab_reports
-- ABDM Concept: DiagnosticReport
-- ==========================================
CREATE TABLE IF NOT EXISTS lab_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    doctor_id UUID REFERENCES doctors(id),
    test_name VARCHAR(200) NOT NULL,
    test_value VARCHAR(100) NOT NULL,
    unit VARCHAR(50),
    reference_range VARCHAR(100),
    is_abnormal BOOLEAN DEFAULT FALSE,
    test_date DATE NOT NULL,
    lab_name VARCHAR(200),
    source_hospital VARCHAR(200),
    source_type VARCHAR(50),
    source_raw_text TEXT,
    abdm_record_type VARCHAR(50) DEFAULT 'DiagnosticReport',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: care_events
-- ABDM Concept: WellnessRecord
-- ==========================================
CREATE TABLE IF NOT EXISTS care_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT NOT NULL,
    reported_by VARCHAR(50) NOT NULL,
    source_type VARCHAR(50),
    source_language VARCHAR(10),
    source_raw_text TEXT,
    severity VARCHAR(20) DEFAULT 'normal',
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    abdm_record_type VARCHAR(50) DEFAULT 'WellnessRecord',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: appointments
-- ==========================================
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    doctor_id UUID REFERENCES doctors(id),
    appointment_date TIMESTAMPTZ NOT NULL,
    appointment_type VARCHAR(100),
    hospital VARCHAR(200),
    prerequisites TEXT[],
    prerequisite_status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: alerts
-- ==========================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT,
    related_medication_ids UUID[],
    related_lab_report_ids UUID[],
    status VARCHAR(20) DEFAULT 'active',
    notified_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: consent_log
-- ABDM Concept: Consent Artifact
-- ==========================================
CREATE TABLE IF NOT EXISTS consent_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    requester_name VARCHAR(200) NOT NULL,
    requester_role VARCHAR(50) NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    records_accessed TEXT[],
    consent_status VARCHAR(20) NOT NULL,
    granted_by VARCHAR(200),
    granted_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    purpose TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- TABLE: daily_briefings
-- ==========================================
CREATE TABLE IF NOT EXISTS daily_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) NOT NULL,
    briefing_date DATE NOT NULL,
    briefing_text TEXT NOT NULL,
    data_sources_used TEXT[],
    confidence_score FLOAT,
    gaps_noted TEXT[],
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- INDEXES
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medications_status ON medications(status);
CREATE INDEX IF NOT EXISTS idx_lab_reports_patient ON lab_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_care_events_patient ON care_events(patient_id);
CREATE INDEX IF NOT EXISTS idx_care_events_type ON care_events(event_type);
CREATE INDEX IF NOT EXISTS idx_alerts_patient ON alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_consent_log_patient ON consent_log(patient_id);

-- ==========================================
-- ROW LEVEL SECURITY
-- ==========================================
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE care_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;

-- Allow all access via service role (used by our backend)
CREATE POLICY "service_role_all" ON patients FOR ALL USING (true);
CREATE POLICY "service_role_all" ON medications FOR ALL USING (true);
CREATE POLICY "service_role_all" ON lab_reports FOR ALL USING (true);
CREATE POLICY "service_role_all" ON care_events FOR ALL USING (true);
CREATE POLICY "service_role_all" ON alerts FOR ALL USING (true);
CREATE POLICY "service_role_all" ON consent_log FOR ALL USING (true);
CREATE POLICY "service_role_all" ON appointments FOR ALL USING (true);
CREATE POLICY "service_role_all" ON daily_briefings FOR ALL USING (true);
CREATE POLICY "service_role_all" ON doctors FOR ALL USING (true);
