-- 0002: retention, member billing standing, legal records, purge log (owner decision 2026-11-17, review T20261117-06).
-- Use ONLY on a database that already ran 0001 (schema_version v=1). Before running: Cloudflare D1 → the database →
-- Time Travel shows a restore point (bookmark) — note the current time so the database can be restored if anything fails.
-- Run the whole file once in the D1 Console. Existing rows are kept; new columns start empty.
alter table requests add column completed_at text;
alter table requests add column purge_body_at text;
alter table requests add column purge_row_at text;
alter table requests add column body_purged_at text;
alter table requests add column legal_hold integer not null default 0;
alter table requests add column legal_until text;
-- existing rows get the safety clock from their creation time
update requests set purge_body_at = strftime('%Y-%m-%dT%H:%M:%fZ', created_at, '+365 days'),
  purge_row_at = strftime('%Y-%m-%dT%H:%M:%fZ', created_at, '+730 days') where purge_body_at is null;

-- Retention clock starts when the owner closes a request (status done / failed / cancelled).
-- Requests never closed: safety limit, text blanked 1 year and record deleted 2 years after creation (owner may shorten).
create trigger if not exists req_close after update of status on requests
when new.status in ('done','failed','cancelled') and old.completed_at is null
begin
  update requests set completed_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    purge_body_at = strftime('%Y-%m-%dT%H:%M:%fZ','now','+90 days'),
    purge_row_at  = strftime('%Y-%m-%dT%H:%M:%fZ','now','+365 days')
  where req_no = new.req_no;
end;
create trigger if not exists req_safety after insert on requests
begin
  update requests set purge_body_at = strftime('%Y-%m-%dT%H:%M:%fZ', new.created_at, '+365 days'),
    purge_row_at = strftime('%Y-%m-%dT%H:%M:%fZ', new.created_at, '+730 days')
  where req_no = new.req_no and purge_body_at is null;
end;
create index if not exists req_purge on requests(purge_body_at);
create index if not exists req_purge_row on requests(legal_hold, purge_row_at);

-- Billing standing of paid members (dates only; no card or account numbers). No row = login role alone decides.
create table if not exists members (
  user_id       text primary key,           -- Netlify Identity user id
  plan          text not null default 'monthly', -- monthly | quarterly | annual
  paid_through  text,                       -- monthly: last paid month 'YYYY-MM' (due on the 1st, KST)
  contract_end  text,                       -- quarterly / annual: last day of the contract 'YYYY-MM-DD' (KST)
  status        text not null default 'active', -- active | suspended
  suspended_at  text,
  updated_at    text,
  note          text
);

-- Purge log: every run (daily worker and on-request) with counts, so a stalled purge is visible.
create table if not exists purge_runs (at text not null, source text, ok integer, body_cleared integer, rows_deleted integer,
  holds_released integer, legal_deleted integer, ip_wiped integer, error text);
create index if not exists purge_at on purge_runs(at);

-- Contract, payment and dispute records, kept apart for the period the law sets (owner fills these by hand).
-- Example periods under the Korean e-commerce consumer protection rules: contract / withdrawal and payment / supply 5 years,
-- complaints and disputes 3 years. Confirm with a legal review before relying on them.
create table if not exists legal_records (
  id            integer primary key autoincrement,
  kind          text not null,              -- contract | payment | dispute
  req_no        text,                       -- related request, if any
  user_key      text,
  summary       text,                       -- only what the law needs (no request text)
  created_at    text not null,
  retain_until  text not null               -- 'YYYY-MM-DD'
);
create index if not exists legal_until on legal_records(retain_until);
-- Daily random salt for the network-address key (deleted after 2 days).
create table if not exists salts (day text primary key, salt text not null);

update schema_version set v=2;
