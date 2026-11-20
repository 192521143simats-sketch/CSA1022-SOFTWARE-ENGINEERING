-- 002 EXPAND phase: additive and backwards-compatible. Release 1.0 code still runs on this schema.
CREATE TABLE policies(
  id INTEGER PRIMARY KEY, campus_code TEXT NOT NULL, policy_version INTEGER NOT NULL,
  max_minutes INTEGER NOT NULL CHECK(max_minutes > 0), temp_limit TEXT NOT NULL,
  UNIQUE(campus_code, policy_version));
INSERT INTO policies(campus_code,policy_version,max_minutes,temp_limit) VALUES
  ('MAIN',1,180,'28.0'),
  ('MAIN',2,180,'28.0'),
  ('NORTH',2,120,'26.5'),
  ('SOUTH',2,240,'30.0');
ALTER TABLE facilities ADD COLUMN campus_code TEXT;
ALTER TABLE bookings ADD COLUMN campus_code TEXT;
ALTER TABLE bookings ADD COLUMN policy_version INTEGER;
ALTER TABLE bookings ADD COLUMN calendar_status TEXT NOT NULL DEFAULT 'NotRequired';
ALTER TABLE tickets ADD COLUMN campus_code TEXT;
ALTER TABLE tickets ADD COLUMN policy_version INTEGER;
CREATE TABLE outbox(
  id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('issue','calendar')),
  ref_id INTEGER NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Synced','NeedsOperator')),
  attempts INTEGER NOT NULL DEFAULT 0, next_attempt_utc TEXT NOT NULL, created_utc TEXT NOT NULL,
  last_error TEXT, remote_id TEXT);
CREATE INDEX idx_outbox_due ON outbox(status, next_attempt_utc);
UPDATE facilities SET campus_code='MAIN';
UPDATE facilities SET campus_code='NORTH' WHERE code='HALL-A';
INSERT INTO facilities(code,name,restricted,campus_code) VALUES ('LAB-S1','South Campus Laboratory S1',0,'SOUTH');
UPDATE bookings SET campus_code='MAIN', policy_version=1;
UPDATE tickets SET campus_code='MAIN', policy_version=1;
INSERT INTO outbox(kind,ref_id,idempotency_key,status,attempts,next_attempt_utc,created_utc)
  SELECT 'issue', id, 'ticket-' || id, 'Pending', 0, created_utc, created_utc FROM tickets WHERE sync_status='Pending';
