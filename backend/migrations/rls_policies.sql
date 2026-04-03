-- backend/migrations/rls_policies.sql
-- Run this in Supabase SQL Editor
-- Go to: supabase.com → your project → SQL Editor → New query

-- ══════════════════════════════════════════════════════════
-- STEP 1: Enable RLS on all tables
-- ══════════════════════════════════════════════════════════

ALTER TABLE schools             ENABLE ROW LEVEL SECURITY;
ALTER TABLE users               ENABLE ROW LEVEL SECURITY;
ALTER TABLE students            ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes             ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance          ENABLE ROW LEVEL SECURITY;
ALTER TABLE marks               ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments         ENABLE ROW LEVEL SECURITY;
ALTER TABLE fee_records         ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications       ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_queue  ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_state         ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents           ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads               ENABLE ROW LEVEL SECURITY;


-- ══════════════════════════════════════════════════════════
-- STEP 2: Helper function to get current school_id
-- Reads from the session variable set by FastAPI
-- ══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION current_school_id()
RETURNS INTEGER AS $$
BEGIN
  -- Reads the school_id set by FastAPI via:
  -- db.execute("SET LOCAL app.school_id = :sid")
  RETURN NULLIF(
    current_setting('app.school_id', TRUE), ''
  )::INTEGER;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;


-- ══════════════════════════════════════════════════════════
-- STEP 3: Create policies for each table
-- Pattern: school_id = current_school_id()
-- ══════════════════════════════════════════════════════════

-- schools: can only see your own school
CREATE POLICY school_isolation ON schools
  FOR ALL USING (id = current_school_id());

-- users: can only see users in your school
CREATE POLICY users_isolation ON users
  FOR ALL USING (school_id = current_school_id());

-- students
CREATE POLICY students_isolation ON students
  FOR ALL USING (school_id = current_school_id());

-- classes
CREATE POLICY classes_isolation ON classes
  FOR ALL USING (school_id = current_school_id());

-- attendance
CREATE POLICY attendance_isolation ON attendance
  FOR ALL USING (school_id = current_school_id());

-- marks
CREATE POLICY marks_isolation ON marks
  FOR ALL USING (school_id = current_school_id());

-- assignments
CREATE POLICY assignments_isolation ON assignments
  FOR ALL USING (school_id = current_school_id());

-- fee_records
CREATE POLICY fee_records_isolation ON fee_records
  FOR ALL USING (school_id = current_school_id());

-- notifications
CREATE POLICY notifications_isolation ON notifications
  FOR ALL USING (school_id = current_school_id());

-- notification_queue
CREATE POLICY notif_queue_isolation ON notification_queue
  FOR ALL USING (school_id = current_school_id());

-- agent_logs
CREATE POLICY agent_logs_isolation ON agent_logs
  FOR ALL USING (school_id = current_school_id());

-- agent_state
CREATE POLICY agent_state_isolation ON agent_state
  FOR ALL USING (school_id = current_school_id());

-- incidents
CREATE POLICY incidents_isolation ON incidents
  FOR ALL USING (school_id = current_school_id());

-- leads
CREATE POLICY leads_isolation ON leads
  FOR ALL USING (school_id = current_school_id());


-- ══════════════════════════════════════════════════════════
-- STEP 4: Allow service role to bypass RLS
-- Your FastAPI backend uses the service role key for writes
-- ══════════════════════════════════════════════════════════

-- Grant the authenticated role access
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;


-- ══════════════════════════════════════════════════════════
-- STEP 5: Test the isolation (run after setup)
-- ══════════════════════════════════════════════════════════

-- Set school context and verify you only see that school's data:
-- SET app.school_id = '1';
-- SELECT * FROM students;  -- should only show school 1 students

-- SET app.school_id = '2';
-- SELECT * FROM students;  -- should only show school 2 students