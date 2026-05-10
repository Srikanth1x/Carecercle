-- CareCircle MVP — Seed Data for Demo
-- Run this AFTER schema.sql in Supabase SQL Editor.

-- ==========================================
-- Patient: Rajesh Sharma (Meera's father)
-- ==========================================
INSERT INTO patients (
    abha_id, abha_address, full_name, date_of_birth, gender, blood_group,
    phone, emergency_contact_name, emergency_contact_phone,
    address_city, address_state, known_conditions, primary_caregiver_telegram_id
) VALUES (
    '12345678901234',
    'rajesh.sharma@carecircle',
    'Rajesh Sharma',
    '1959-03-15',
    'Male',
    'B+',
    '+91-9800000001',
    'Meera Sharma',
    '+91-9800000002',
    'Lucknow',
    'Uttar Pradesh',
    ARRAY['Type 2 Diabetes', 'Hypertension', 'Cardiac History (minor episode 6 months ago)'],
    'MEERA_CHAT_ID_PLACEHOLDER'
) ON CONFLICT (abha_id) DO NOTHING;

-- ==========================================
-- Doctors
-- ==========================================
INSERT INTO doctors (name, specialty, hospital, phone, emergency_phone) VALUES
    ('Dr. Anil Kapoor', 'Cardiologist', 'City Heart Hospital, Lucknow', '+91-9800000010', '+91-9800000010'),
    ('Dr. Priya Mehta', 'Endocrinologist', 'Diabetes Care Center, Lucknow', '+91-9800000011', '+91-9800000011'),
    ('Dr. Suresh Verma', 'General Physician', 'Lucknow Medical Clinic', '+91-9800000012', '+91-9800000012')
ON CONFLICT DO NOTHING;

-- ==========================================
-- Medications (active)
-- ==========================================
DO $$
DECLARE
    patient_uuid UUID;
    dr_kapoor_uuid UUID;
    dr_mehta_uuid UUID;
    dr_verma_uuid UUID;
BEGIN
    SELECT id INTO patient_uuid FROM patients WHERE abha_id = '12345678901234';
    SELECT id INTO dr_kapoor_uuid FROM doctors WHERE name = 'Dr. Anil Kapoor';
    SELECT id INTO dr_mehta_uuid FROM doctors WHERE name = 'Dr. Priya Mehta';
    SELECT id INTO dr_verma_uuid FROM doctors WHERE name = 'Dr. Suresh Verma';

    INSERT INTO medications (patient_id, doctor_id, drug_name, dosage, frequency, timing, purpose, status, prescribed_date, source_type) VALUES
        (patient_uuid, dr_mehta_uuid, 'Metformin', '500mg', 'twice daily', 'after meals', 'blood sugar control', 'active', '2024-01-15', 'manual'),
        (patient_uuid, dr_mehta_uuid, 'Glimepiride', '2mg', 'once daily', 'before breakfast', 'blood sugar control', 'active', '2024-01-15', 'manual'),
        (patient_uuid, dr_kapoor_uuid, 'Amlodipine', '5mg', 'once daily', 'morning', 'blood pressure control', 'active', '2024-02-10', 'manual'),
        (patient_uuid, dr_kapoor_uuid, 'Aspirin', '75mg', 'once daily', 'after lunch', 'cardiac protection', 'active', '2024-02-10', 'manual'),
        (patient_uuid, dr_kapoor_uuid, 'Atorvastatin', '10mg', 'once daily', 'at night', 'cholesterol control', 'active', '2024-02-10', 'manual');

    -- ==========================================
    -- Lab Reports (recent, mostly abnormal)
    -- ==========================================
    INSERT INTO lab_reports (patient_id, test_name, test_value, unit, reference_range, is_abnormal, test_date, source_type) VALUES
        (patient_uuid, 'Fasting Blood Sugar', '180', 'mg/dL', '70-110 mg/dL', TRUE, CURRENT_DATE - INTERVAL '21 days', 'manual'),
        (patient_uuid, 'HbA1c', '8.2', '%', '<7%', TRUE, CURRENT_DATE - INTERVAL '42 days', 'manual'),
        (patient_uuid, 'Blood Pressure Systolic', '150', 'mmHg', '<130 mmHg', TRUE, CURRENT_DATE - INTERVAL '14 days', 'manual'),
        (patient_uuid, 'Blood Pressure Diastolic', '95', 'mmHg', '<85 mmHg', TRUE, CURRENT_DATE - INTERVAL '14 days', 'manual'),
        (patient_uuid, 'Total Cholesterol', '220', 'mg/dL', '<200 mg/dL', TRUE, CURRENT_DATE - INTERVAL '42 days', 'manual'),
        (patient_uuid, 'Serum Creatinine', '1.1', 'mg/dL', '0.7-1.3 mg/dL', FALSE, CURRENT_DATE - INTERVAL '42 days', 'manual');

    -- ==========================================
    -- Upcoming Appointment
    -- ==========================================
    INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_type, hospital, prerequisites, prerequisite_status, status) VALUES
        (patient_uuid, dr_kapoor_uuid, CURRENT_DATE + INTERVAL '10 days', 'Follow-up', 'City Heart Hospital, Lucknow',
         ARRAY['Recent blood test (fasting blood sugar, lipid panel)'], 'pending', 'scheduled');

    -- ==========================================
    -- Sample Care Events
    -- ==========================================
    INSERT INTO care_events (patient_id, event_type, event_description, reported_by, source_type, severity, event_timestamp) VALUES
        (patient_uuid, 'symptom', 'Dizziness in the morning', 'caregiver', 'text_message', 'attention', NOW() - INTERVAL '18 hours'),
        (patient_uuid, 'meal', 'Skipped breakfast', 'caregiver', 'text_message', 'attention', NOW() - INTERVAL '18 hours'),
        (patient_uuid, 'medication_taken', 'All medicines taken', 'caregiver', 'text_message', 'normal', NOW() - INTERVAL '18 hours');

END $$;
