-- GOV RADAR member requests (Cloudflare D1, free plan). FRESH database only: run once in Cloudflare → D1 → Console.
-- A database made from an older version must be updated with cf/d1/migrations/ in order instead (re-running this file adds no columns).
-- One row per request. counted=1 uses the monthly allowance; the owner sets counted=0 to give it back (failed or cancelled).
-- Personal data: email and request text. Keep only as long as the privacy policy says; delete with: delete from requests where created_at < '<date>'.
create table if not exists requests (
  req_no     text primary key,              -- RQ-YYMMDD-XXXXXXXX (random), made by the server
  created_at text not null,                 -- ISO time (UTC)
  month      text not null,                 -- YYYY-MM in Korea time, for the monthly allowance
  user_key   text not null,                 -- 'u:<identity id>' when signed in, else 'e:<sha256(email)>'
  email      text not null,
  grade      text,                          -- m0..m5 from the login (app_metadata.roles)
  type       text not null,                 -- tender | country | family | partner
  lang       text,
  body       text not null,                 -- the request text (no health details are asked for)
  dedupe     text not null,                 -- hash of type+body+email: same request within 10 minutes is not counted twice
  counted    integer not null default 0,    -- 1 = uses one of the monthly requests
  status     text not null default 'received', -- received | client_ok | client_fail (browser's own report, not a confirmed delivery) | in_progress | done | failed | cancelled
  note       text,
  relay_key  text,                          -- sha256 of the one-time token given to the sender; cleared after the relay report
  ip_hash    text,                          -- network address keyed with a daily random salt (salts table), only for the daily limit; wiped after 48 h
  completed_at   text,                      -- set when status becomes done | failed | cancelled (trigger below)
  purge_body_at  text,                      -- completed_at + 90 days: request text, email, note are blanked
  purge_row_at   text,                      -- completed_at + 1 year: the minimal record is deleted
  body_purged_at text,                      -- when the text was blanked
  legal_hold     integer not null default 0, -- 1 = tied to a contract, payment or dispute: keeps ONLY the minimal record, ONLY until legal_until
  legal_until    text                      -- 'YYYY-MM-DD' end of the legal period; empty or past -> hold released by the purge
);
create index if not exists req_ip on requests(ip_hash, created_at);
create index if not exists req_user_month on requests(user_key, month);
create index if not exists req_dedupe on requests(user_key, dedupe, created_at);

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

-- Version marker (migrations check it).
create table if not exists schema_version (v integer not null);
insert into schema_version (v) select 2 where not exists (select 1 from schema_version);
