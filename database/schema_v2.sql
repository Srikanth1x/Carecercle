-- CareCircle — Multi-User Migration
-- Run this in Supabase SQL Editor AFTER schema.sql

-- 1. Link patients to the Supabase auth user who owns them
ALTER TABLE patients ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);

-- 2. Map Supabase auth user to their Telegram chat_id
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    telegram_chat_id VARCHAR(50) UNIQUE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON user_profiles FOR ALL USING (true);

-- After creating your account via /register on the web, run this to link your seed data:
-- UPDATE patients SET user_id = '<your-auth-user-uuid>' WHERE abha_id = '12345678901234';
-- INSERT INTO user_profiles (user_id) VALUES ('<your-auth-user-uuid>') ON CONFLICT DO NOTHING;
