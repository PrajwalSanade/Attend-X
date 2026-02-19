-- Enable RLS
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- Create admins table if not exists (already in schema but ensuring structure)
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL, -- references auth.users.id
    name TEXT,
    email TEXT UNIQUE,
    college TEXT,
    role TEXT DEFAULT 'admin',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update students table
ALTER TABLE students 
ADD COLUMN IF NOT EXISTS admin_id UUID REFERENCES admins(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS face_registered BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- Create face_encodings table
CREATE TABLE IF NOT EXISTS face_encodings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    encoding JSONB NOT NULL, -- Storing as JSON array
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_student_encoding UNIQUE (student_id)
);

-- Update attendance table
ALTER TABLE attendance 
ADD COLUMN IF NOT EXISTS admin_id UUID REFERENCES admins(id) ON DELETE CASCADE;

-- RLS Policies

-- Admin can see only their own data
CREATE POLICY "Admins can view their own students" ON students
    FOR ALL
    USING (admin_id IN (SELECT id FROM admins WHERE user_id = auth.uid()));

CREATE POLICY "Admins can view their own attendance" ON attendance
    FOR ALL
    USING (admin_id IN (SELECT id FROM admins WHERE user_id = auth.uid()));

-- Students can view their own data (optional, for student dashboard)
CREATE POLICY "Students can view their own record" ON students
    FOR SELECT
    USING (id::text = current_setting('request.jwt.claim.sub', true) OR roll_number = current_setting('app.current_roll', true));

-- Fix system_settings
CREATE TABLE IF NOT EXISTS system_settings (
  id INTEGER PRIMARY KEY DEFAULT 1,
  student_auth_enabled BOOLEAN NOT NULL DEFAULT true,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by TEXT,
  CONSTRAINT single_row_only CHECK (id = 1)
);

INSERT INTO system_settings (id, student_auth_enabled) VALUES (1, true) ON CONFLICT (id) DO NOTHING;
