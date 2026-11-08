-- GOV RADAR · Supabase schema (free tier). Run once in Supabase → SQL Editor.
-- Visitors read the static site. Signed-in members can save tenders, follow countries,
-- keep a company profile and receive alerts. Premium (M3, M4, M5) can read Foresight.

create table if not exists public.profiles (
  user_id uuid primary key references auth.users on delete cascade,
  company text, industries text[] default '{}', revenue_100m numeric, years int, projects int, employees int,
  certs text[] default '{}', email text, lang text default 'ko',
  alert_email boolean default true,          -- weekly + instant email alerts
  kakao_phone text, alert_kakao boolean default false,   -- KakaoTalk AlimTalk (needs consent)
  slack_webhook text, teams_webhook text,    -- B2B: company channel alerts
  marketing_consent boolean default false, consent_at timestamptz,
  created_at timestamptz default now(), updated_at timestamptz default now()
);
create table if not exists public.members (     -- set by WMM only (service role)
  user_id uuid primary key references auth.users on delete cascade,
  tier text check (tier in ('M1','M2','M3','M4','M5')), since date default current_date
);
create table if not exists public.follows (
  user_id uuid references auth.users on delete cascade, iso char(2), lang text default 'ko',
  created_at timestamptz default now(), primary key (user_id, iso)
);
create table if not exists public.watch (
  user_id uuid references auth.users on delete cascade, iso char(2), title text, deadline date,
  created_at timestamptz default now(), primary key (user_id, iso, title)
);
create table if not exists public.foresight ( id text primary key, body jsonb not null, updated_at timestamptz default now() );
create table if not exists public.alert_log ( user_id uuid, item_key text, channel text, sent_at timestamptz default now(), primary key (user_id, item_key, channel) );
create table if not exists public.ask_usage ( user_id uuid, day date default current_date, n int default 0, primary key (user_id, day) );

alter table public.profiles  enable row level security;
alter table public.members   enable row level security;
alter table public.follows   enable row level security;
alter table public.watch     enable row level security;
alter table public.foresight enable row level security;
alter table public.alert_log enable row level security;
alter table public.ask_usage enable row level security;

create policy "own profile"  on public.profiles for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own follows"  on public.follows  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own watch"    on public.watch    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "read own tier" on public.members for select using (auth.uid() = user_id);
create policy "premium reads foresight" on public.foresight for select
  using (exists (select 1 from public.members m where m.user_id = auth.uid() and m.tier in ('M3','M4','M5')));
-- alert_log and ask_usage: no client policies → only the server (service role) can read/write.
