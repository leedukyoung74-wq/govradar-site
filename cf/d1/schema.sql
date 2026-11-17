-- GOV RADAR member requests (Cloudflare D1, free plan). Run once in Cloudflare → D1 → govradar → Console.
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
  status     text not null default 'received', -- received | relayed | relay_failed | in_progress | done | failed | cancelled
  note       text,
  relay_key  text,                          -- sha256 of the one-time token given to the sender; cleared after the relay report
  ip_hash    text                           -- sha256 of the network address, only for the daily request limit
);
create index if not exists req_ip on requests(ip_hash, created_at);
create index if not exists req_user_month on requests(user_key, month);
create index if not exists req_dedupe on requests(user_key, dedupe, created_at);
