-- ============================================
-- SYSTEM SETTINGS TABLE
-- ============================================
-- This table stores system-wide settings like
-- student authentication toggle
-- ============================================

-- Create system_settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    student_auth_enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),
    CONSTRAINT single_row CHECK (id = 1)
);

-- Insert default row if not exists
INSERT INTO system_settings (id, student_auth_enabled, updated_at)
VALUES (1, TRUE, NOW())
ON CONFLICT (id) DO NOTHING;

-- Enable RLS
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read system settings
CREATE POLICY "Anyone can read system settings"
ON system_settings
FOR SELECT
USING (true);

-- Policy: Only authenticated users can update system settings
CREATE POLICY "Authenticated users can update system settings"
ON system_settings
FOR UPDATE
USING (auth.role() = 'authenticated')
WITH CHECK (auth.role() = 'authenticated');

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_system_settings_id ON system_settings(id);

-- Add comment
COMMENT ON TABLE system_settings IS 'System-wide settings including student authentication toggle';
COMMENT ON COLUMN system_settings.student_auth_enabled IS 'Controls whether students can login and mark attendance';
COMMENT ON COLUMN system_settings.updated_by IS 'Admin user who last updated the settings';

-- Grant permissions
GRANT SELECT ON system_settings TO anon, authenticated;
GRANT UPDATE ON system_settings TO authenticated;
