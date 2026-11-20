-- 001: release 1.0 schema + synthetic reference data
CREATE TABLE facilities(
  id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
  restricted INTEGER NOT NULL DEFAULT 0);
CREATE TABLE bookings(
  id INTEGER PRIMARY KEY,
  facility_id INTEGER NOT NULL REFERENCES facilities(id),
  requester TEXT NOT NULL, title TEXT NOT NULL,
  start_utc TEXT NOT NULL, end_utc TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Pending', created_utc TEXT NOT NULL);
CREATE INDEX idx_bookings_fac ON bookings(facility_id, start_utc);
CREATE TABLE tickets(
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT,
  category TEXT NOT NULL, impact TEXT NOT NULL, urgency TEXT NOT NULL,
  priority TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
  notes TEXT, source TEXT, event_id TEXT,
  facility_id INTEGER REFERENCES facilities(id),
  reporter TEXT NOT NULL, created_utc TEXT NOT NULL, sla_due_utc TEXT NOT NULL,
  sync_status TEXT NOT NULL DEFAULT 'Pending', remote_id TEXT,
  UNIQUE(source, event_id));
CREATE TABLE audit(
  id INTEGER PRIMARY KEY, ticket_id INTEGER, booking_id INTEGER,
  action TEXT NOT NULL, from_state TEXT, to_state TEXT,
  actor TEXT NOT NULL, role TEXT NOT NULL, at_utc TEXT NOT NULL);
-- synthetic reference data
INSERT INTO facilities(code,name,restricted) VALUES
  ('LAB-204','Chemistry Laboratory 204',1),
  ('ROOM-101','Lecture Room 101',0),
  ('HALL-A','Seminar Hall A',0);
