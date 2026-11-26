-- GOV RADAR member requests (Cloudflare D1, free plan). Run once in Cloudflare → D1 → govradar → Console.
-- One row per request. counted=1 uses the monthly allowance; set counted=0 to give it back (failed or cancelled).
create table if not exists requests (
  req_no     text primary key,              -- RQ-YYMMDD-XXXX, made by the server
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
  status     text not null default 'received', -- received | gateway_reported | gateway_failed_reported | relayed (legacy) | relay_failed (legacy) | in_progress | done | failed | cancelled
  note       text
);
create index if not exists req_user_month on requests(user_key, month);
create index if not exists req_dedupe on requests(user_key, dedupe, created_at);
