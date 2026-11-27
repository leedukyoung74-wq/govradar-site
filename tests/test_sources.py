"""Offline tests for the tender collectors (no network, no secrets). Run: python -m unittest discover -s tests -v"""
import datetime, json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, ROOT)
import feed_more as FM
import feed_tenders as FT
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "sources"))
import summary as SUM

UTC = datetime.timezone.utc
def item(**k):
    base = {"iso": "GB", "title": "Road maintenance framework", "buyer": "Council A", "deadline": "2027-06-10", "deadline_at": "2027-06-10",
            "url": "https://example.org/n/1", "sid": "N-1", "source": "UK Find a Tender"}
    base.update(k); return base


class Deadlines(unittest.TestCase):
    def test_impossible_date_rejected(self):
        self.assertEqual(FM.parse_deadline("2026-02-31"), (None, None))
        self.assertEqual(FT.valid(item(deadline="2026-02-31", deadline_at="2026-02-31")), "bad-deadline")

    def test_formats(self):
        d, at = FM.parse_deadline("2026-11-23T17:00:00Z"); self.assertEqual(at, datetime.datetime(2026, 11, 23, 17, 0, tzinfo=UTC))
        d, at = FM.parse_deadline("2026-12-10+02:00"); self.assertEqual(at.utcoffset(), datetime.timedelta(hours=2)); self.assertEqual(at.hour, 23)
        d, at = FM.parse_deadline("2026-12-15T14:00:00"); self.assertEqual(str(d), "2026-12-15"); self.assertIsNone(at)
        self.assertEqual(FM.parse_deadline("next week"), (None, None))

    def test_d0_kept_until_the_published_time(self):
        raw = "2026-11-16T10:00:00+09:00"  # 10:00 in Seoul = 01:00 UTC
        self.assertTrue(FM.still_open(raw, datetime.datetime(2026, 11, 16, 0, 30, tzinfo=UTC)))
        self.assertFalse(FM.still_open(raw, datetime.datetime(2026, 11, 16, 1, 30, tzinfo=UTC)))

    def test_d0_without_timezone_kept_all_day_everywhere(self):
        # date-only deadlines stay until the date has ended in UTC-12, so nothing live is dropped early
        self.assertTrue(FM.still_open("2026-11-16", datetime.datetime(2026, 11, 16, 23, 0, tzinfo=UTC)))
        self.assertTrue(FM.still_open("2026-11-16", datetime.datetime(2026, 11, 17, 11, 0, tzinfo=UTC)))
        self.assertFalse(FM.still_open("2026-11-16", datetime.datetime(2026, 11, 17, 12, 30, tzinfo=UTC)))

    def test_d1_d2_kept_and_past_dropped(self):
        now = datetime.datetime(2026, 11, 16, 3, 0, tzinfo=UTC)
        self.assertEqual(FT.valid(item(deadline="2026-11-17", deadline_at="2026-11-17"), now), "")
        self.assertEqual(FT.valid(item(deadline="2026-11-18", deadline_at="2026-11-18T12:00:00Z"), now), "")
        self.assertEqual(FT.valid(item(deadline="2026-11-14", deadline_at="2026-11-14"), now), "closed")

    def test_far_and_missing(self):
        self.assertEqual(FT.valid(item(deadline="2099-01-01", deadline_at="2099-01-01")), "far-deadline")
        self.assertEqual(FT.valid(item(title="")), "missing-field")
        self.assertEqual(FT.valid(item(url="ftp://x")), "missing-field")


class Dedup(unittest.TestCase):
    def test_lookalikes_are_not_deleted(self):
        # same title and deadline, but different buyer / lot / notice id -> all five must stay
        g = [item(sid="TED-1", url="https://ted.europa.eu/1", buyer="Ville de Lyon", source="EU TED", iso="FR"),
             item(sid="TED-2", url="https://ted.europa.eu/2", buyer="Ville de Nice", source="EU TED", iso="FR"),
             item(sid="TED-3", url="https://ted.europa.eu/3", buyer="Ville de Lyon", title="Road maintenance framework - Lot 2", source="EU TED", iso="FR"),
             item(sid="TED-4", url="https://ted.europa.eu/4", buyer="Ville de Lyon", title="Road maintenance framework - Lot 3", source="EU TED", iso="FR"),
             item(sid="TED-5", url="https://ted.europa.eu/5", buyer="Region Sud", source="EU TED", iso="FR")]
        items, c = FT.merge([("EU TED", g)])
        self.assertEqual(len(items), 5); self.assertEqual(c["EU TED"]["duplicates"], 0)

    def test_same_notice_id_is_a_confirmed_duplicate(self):
        g = [item(sid="ABC", url="https://a.org/1"), item(sid="ABC", url="https://a.org/1?v=2")]
        items, c = FT.merge([("UK Find a Tender", g)])
        self.assertEqual(len(items), 1); self.assertEqual(c["UK Find a Tender"]["duplicates"], 1)

    def test_same_url_is_a_confirmed_duplicate(self):
        g = [item(sid="", url="https://A.org/n/9/"), item(sid="", url="https://a.org/n/9")]
        items, _ = FT.merge([("X", g)]); self.assertEqual(len(items), 1)

    def test_cross_source_lookalike_kept_and_flagged(self):
        a = item(sid="FTS-1", url="https://fts/1", source="UK Find a Tender")
        b = item(sid="CF-1", url="https://cf/1", source="UK Contracts Finder")
        items, c = FT.merge([("UK Find a Tender", [a]), ("UK Contracts Finder", [b])])
        self.assertEqual(len(items), 2); self.assertEqual(items[1].get("dupc"), "https://fts/1"); self.assertEqual(c["UK Contracts Finder"]["flagged_similar"], 1)


class Status(unittest.TestCase):
    def test_states(self):
        self.assertEqual(FT.classify_state({"skipped": True}), "SKIPPED")
        self.assertEqual(FT.classify_state({"requests": 3, "failed": 3, "raw": 0}), "ERROR")
        self.assertEqual(FT.classify_state({"requests": 3, "failed": 1, "raw": 50}), "PARTIAL")
        self.assertEqual(FT.classify_state({"requests": 1, "failed": 0, "raw": 0}), "EMPTY_SUCCESS")
        self.assertEqual(FT.classify_state({"requests": 2, "failed": 0, "raw": 10}), "SUCCESS")


class Sources(unittest.TestCase):
    def test_contracts_finder_url(self):
        self.assertEqual(FM.cf_notice_url("42c80b0b-fbe7-49d7-8ac2-07a1a30e6e1a-921337"),
                         "https://www.contractsfinder.service.gov.uk/Notice/42c80b0b-fbe7-49d7-8ac2-07a1a30e6e1a")
        self.assertEqual(FM.cf_notice_url("not-a-uuid"), "")

    def test_ted_item_d0_and_size(self):
        today = FM.TODAY.isoformat()
        n = {"publication-number": "1-2026", "notice-title": {"eng": "France – Works – Bridge"}, "buyer-name": {"fra": ["Ville"]},
             "buyer-country": ["FRA"], "deadline-receipt-tender-date-lot": [today + "-12:00"], "contract-nature": ["works"],
             "estimated-value-proc": "3000000", "estimated-value-cur-proc": "EUR"}
        it = FM.ted_item(n, 2e6)
        self.assertIsNotNone(it); self.assertEqual(it["iso"], "FR"); self.assertEqual(it["title"], "Works – Bridge"); self.assertEqual(it["sid"], "1-2026")
        self.assertIsNone(FM.ted_item(dict(n, **{"estimated-value-proc": "100"}), 2e6))

    def test_mask_hides_keys(self):
        os.environ["SAM_KEY"] = "SECRET123"
        try:
            s = FM.mask("HTTP Error 403 for https://api.sam.gov/x?api_key=SECRET123&limit=1 and SECRET123")
            self.assertNotIn("SECRET123", s); self.assertIn("api_key=***", s)
            self.assertIn("serviceKey=***", FM.mask("https://apis.data.go.kr/a?serviceKey=abc%2Bdef&pageNo=1"))
        finally:
            del os.environ["SAM_KEY"]


class Registry(unittest.TestCase):
    def setUp(self):
        self.reg = json.load(open(os.path.join(ROOT, "tools", "sources", "registry.json"), encoding="utf8"))

    def test_summary_file_matches_registry(self):
        got = open(os.path.join(ROOT, "tools", "sources", "SUMMARY.md"), encoding="utf8").read()
        self.assertEqual(got, SUM.render(self.reg), "run python tools/sources/summary.py")

    def test_ids_unique_and_fields(self):
        ids = [s["id"] for s in self.reg]; self.assertEqual(len(ids), len(set(ids)))
        for s in self.reg:
            self.assertIn(s["collect"], ("PASS", "FAIL", "UNKNOWN"))
            if s["collect"] == "PASS": self.assertTrue(s["url"].startswith("https://"))

    def test_robots_never_none(self):
        self.assertFalse([s["id"] for s in self.reg if s.get("robots") == "none"])


if __name__ == "__main__":
    unittest.main()


class NoKeys(unittest.TestCase):
    def test_keyed_sources_skip_cleanly_without_keys(self):
        saved = {k: os.environ.pop(k, None) for k in ("DAPA_KEY", "SAM_KEY")}
        try:
            FM.STATS.clear()
            self.assertEqual(FM.dapa(), []); self.assertEqual(FM.sam(), [])
            self.assertEqual(FT.classify_state(FM.stat("DAPA (Korea)")), "SKIPPED")
            self.assertEqual(FT.classify_state(FM.stat("SAM.gov (US)")), "SKIPPED")
            self.assertEqual(FM.stat("DAPA (Korea)")["requests"], 0)  # no network call at all
        finally:
            for k, v in saved.items():
                if v: os.environ[k] = v


class Retry(unittest.TestCase):
    def test_timeout_then_success_is_not_a_failure(self):
        import time
        FM.STATS.clear(); calls = {"n": 0}; real = time.sleep; time.sleep = lambda s: None
        def flaky():
            calls["n"] += 1
            if calls["n"] < 2: raise TimeoutError("The read operation timed out")
            return "ok"
        try: self.assertEqual(FM._retry("T", flaky), "ok")
        finally: time.sleep = real
        self.assertEqual(FM.stat("T")["failed"], 0); self.assertEqual(FM.stat("T")["requests"], 1)

    def test_http_404_is_not_retried(self):
        import urllib.error
        FM.STATS.clear(); calls = {"n": 0}
        def nf():
            calls["n"] += 1; raise urllib.error.HTTPError("u", 404, "nf", {}, None)
        with self.assertRaises(Exception): FM._retry("T", nf)
        self.assertEqual(calls["n"], 1); self.assertEqual(FM.stat("T")["failed"], 1)


class FindATenderTimeout(unittest.TestCase):
    """Replays the 2026-11-16 06:19Z production failure: the first Find a Tender request timed out."""
    def test_uk_survives_one_read_timeout(self):
        import io, time, urllib.request
        dl = (FM.TODAY + datetime.timedelta(days=20)).isoformat() + "T12:00:00Z"
        pkg = {"releases": [{"id": "000001-2026", "ocid": "ocds-h6vhtk-000001", "buyer": {"name": "Council A"},
                             "tender": {"status": "active", "title": "Bridge works", "tenderPeriod": {"endDate": dl},
                                        "value": {"amount": 5000000, "currency": "GBP"}, "mainProcurementCategory": "works"}}], "links": {}}
        calls = {"n": 0}
        class R(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False
        def fake(req, timeout=0):
            calls["n"] += 1
            if calls["n"] == 1: raise TimeoutError("The read operation timed out")
            return R(json.dumps(pkg).encode())
        real_open, real_sleep = urllib.request.urlopen, time.sleep
        urllib.request.urlopen, time.sleep = fake, (lambda s: None)
        try:
            FM.STATS.clear(); got = FM.uk()
        finally:
            urllib.request.urlopen, time.sleep = real_open, real_sleep
        self.assertEqual(len(got), 1); self.assertEqual(got[0]["title"], "Bridge works")
        st = FM.stat("UK Find a Tender")
        self.assertEqual(st["failed"], 0); self.assertEqual(FT.classify_state(st), "PARTIAL")  # recovered HTTP is not complete UK coverage
        self.assertTrue(any(n.startswith("retry 1") for n in st["notes"]))

    def test_rate_limit_waits_for_retry_after(self):
        import time, urllib.error
        waits = []; real = time.sleep; time.sleep = lambda s: waits.append(s); calls = {"n": 0}
        def rl():
            calls["n"] += 1
            if calls["n"] == 1: raise urllib.error.HTTPError("u", 429, "Too Many Requests", {"Retry-After": "90"}, None)
            return "ok"
        try: self.assertEqual(FM._retry("T2", rl), "ok")
        finally: time.sleep = real
        self.assertEqual(waits, [90])


import quality_gate as QG
import verify_samples as VS

def feed(n, src="World Bank", start=0, stamp=None, iso_cycle=("GB", "FR", "DE", "KE")):
    now = datetime.datetime.now(datetime.timezone.utc)
    items = [item(sid=f"S{i}", url=f"https://x.org/{src}/{i}", source=src, iso=iso_cycle[i % len(iso_cycle)], slug="s", n={}, added="2026-11-16", sec=[], pg="")
             for i in range(start, start + n)]
    return {"updated": stamp or now.strftime("%Y-%m-%dT%H:%MZ"), "count": len(items), "items": items}


class QualityGate(unittest.TestCase):
    def test_good_feed_passes(self):
        self.assertEqual(QG.check({"tenders.json": feed(300)}, {"tenders.json": feed(280)}), [])

    def test_big_drop_blocks(self):
        bad = QG.check({"tenders.json": feed(150)}, {"tenders.json": feed(900)})
        self.assertTrue(any("drop" in b for b in bad))

    def test_vanished_source_blocks(self):
        old = feed(200); old["items"] += feed(40, src="EU TED", start=500)["items"]; old["count"] = len(old["items"])
        bad = QG.check({"tenders.json": feed(250)}, {"tenders.json": old})
        self.assertTrue(any("EU TED" in b for b in bad))

    def test_invalid_rows_and_duplicates_block(self):
        f = feed(200); f["items"][0]["deadline"] = f["items"][0]["deadline_at"] = "2026-02-31"; f["items"][1]["url"] = f["items"][2]["url"]
        bad = QG.check({"tenders.json": f}, {})
        self.assertTrue(any("invalid" in b for b in bad)); self.assertTrue(any("duplicate" in b for b in bad))

    def test_missing_field_and_stale_stamp_block(self):
        f = feed(200, stamp="2026-01-01T00:00Z"); del f["items"][5]["slug"]
        bad = QG.check({"tenders.json": f}, {})
        self.assertTrue(any("missing:slug" in b for b in bad)); self.assertTrue(any("old" in b for b in bad))

    def test_unreadable_blocks(self):
        self.assertEqual(QG.check({"tenders.json": None}, {}), ["tenders.json missing or unreadable"])


class LinkAndRecord(unittest.TestCase):
    def j(self, code, unavailable=False, title=True, dl=True):
        return VS.judge({"url_status": code, "record_unavailable": unavailable, "title_ok": title, "deadline_ok": dl})

    def test_broken_link_fails_even_if_record_unavailable(self):
        r = self.j(404, unavailable=True); self.assertEqual((r["link"], r["record"], r["verdict"]), ("broken", "unavailable", "FAIL"))

    def test_403_is_never_success(self):
        r = self.j(403); self.assertEqual((r["link"], r["verdict"]), ("unconfirmed", "UNKNOWN"))

    def test_pass_needs_both(self):
        self.assertEqual(self.j(200)["verdict"], "PASS")
        self.assertEqual(self.j(200, unavailable=True)["verdict"], "UNKNOWN")
        self.assertEqual(self.j(200, dl=False)["verdict"], "FAIL")

    def test_temporary_errors_are_unknown(self):
        for c in (429, 503, "TimeoutError"): self.assertEqual(self.j(c)["link"], "unknown")


class OfficialGate(unittest.TestCase):
    def test_official_all_failed_blocks(self):
        o = {"sources": {k: {"ok": False} for k in ("usgs", "gdacs", "eonet", "who", "cneos", "swpc")}, "items": {}}
        self.assertTrue(any("official" in b for b in QG.check({"tenders.json": feed(300), "hz/official.json": o}, {})))

    def test_official_partial_ok_passes(self):
        o = {"sources": {"usgs": {"ok": True}, "gdacs": {"ok": False}}, "items": {"usgs": []}}
        self.assertEqual(QG.check({"tenders.json": feed(300), "hz/official.json": o}, {}), [])


class Econ(unittest.TestCase):
    def setUp(self):
        import feed_econ as FE; self.FE = FE

    def test_aggregates_skipped_and_values_kept(self):
        j = [{}, [{"countryiso3code": "AFE", "date": "2025", "value": 1.0}, {"countryiso3code": "KOR", "date": "2025", "value": 36227.4},
                  {"countryiso3code": "NGA", "date": "2024", "value": None}]]
        self.assertEqual(self.FE.parse_wb(j), {"KR": [36227.0, "2025"]})

    def test_bad_fx_answer_raises(self):
        with self.assertRaises(ValueError): self.FE.parse_fx({"result": "error"})

    def test_gate(self):
        good = {"c": {f"C{i}": {"gdp": [1, "2025"], "usd": 2} for i in range(160)} | {"KR": {"gdp": [1, "2025"], "usd": 1336}}, "src": {"fx": {"ok": True}}}
        self.assertEqual(QG.check({"tenders.json": feed(300), "econ.json": good}, {}), [])
        bad = {"c": {"KR": {"gdp": [1, "2025"], "usd": 1.3}}, "src": {"fx": {"ok": False}}}
        b = QG.check({"tenders.json": feed(300), "econ.json": bad}, {})
        self.assertEqual(len([x for x in b if "econ" in x]), 4)


class Sanctions(unittest.TestCase):
    def setUp(self):
        import feed_sanctions as FS; self.FS = FS

    def test_country_names(self):
        for n, c in [("Korea, North", "KP"), ("Burma", "MM"), ("St Kitts and Nevis", "KN"), ("Côte d'Ivoire", "CI"), ("United Kingdom", "GB"), ("France", "FR"), ("Region: Crimea", "UA")]:
            self.assertEqual(self.FS.iso(n), c, n)
        self.assertIsNone(self.FS.iso("-0-"))

    def test_us_parse_and_tally(self):
        sdn = b'36,"AEROCARIBBEAN AIRLINES",-0- ,"CUBA",-0-\n306,"BANCO",-0- ,"CUBA] [SDGT",-0-\n'
        add = b'36,25,-0- ,"Havana","Cuba",-0-\n306,199,"x","Zurich","Switzerland",-0-\n306,200,"y","Havana","Cuba",-0-\n'
        e, miss = self.FS.parse_us(sdn, add)
        n, prog = self.FS.tally(e)
        self.assertEqual((n["CU"], n["CH"]), (2, 1)); self.assertEqual(prog["CU"][0], "CUBA")

    def test_uk_regime_short(self):
        self.assertEqual(self.FS.short_uk("The Russia (Sanctions) (EU Exit) Regulations 2019"), "Russia")

    def test_gate(self):
        ok = {"c": {f"C{i}": {"us": [1, []]} for i in range(120)} | {"KP": {"un": [141, ["DPRK"]]}}, "src": {"un": {"ok": True}}}
        self.assertEqual(QG.check({"tenders.json": feed(300), "sanctions.json": ok}, {}), [])
        b = QG.check({"tenders.json": feed(300), "sanctions.json": {"c": {}, "src": {}}}, {})
        self.assertEqual(len([x for x in b if "sanctions" in x]), 3)


class Active(unittest.TestCase):
    def test_us_date(self):
        import feed_intel as FI
        self.assertEqual(FI.us_date("12/31/2025"), "2025-12-31"); self.assertEqual(FI.us_date("2027-06-30T00:00:00Z"), "2027-06-30"); self.assertEqual(FI.us_date(None), "")

    def test_gate_active_minimum(self):
        b = QG.check({"tenders.json": feed(300), "active.json": {"items": [{}] * 10}}, {})
        self.assertTrue(any("active.json" in x for x in b))


class Today(unittest.TestCase):
    def test_dates(self):
        import feed_today as FT
        self.assertEqual(FT.iso_date("2026-Nov-21 04:10"), "2026-11-21"); self.assertEqual(FT.iso_date("2026-11-13"), "2026-11-13"); self.assertEqual(FT.iso_date("x"), "")

    def test_gate(self):
        self.assertEqual(QG.check({"tenders.json": feed(300), "today.json": {"n": {"open": 300}}}, {}), [])
        self.assertTrue(QG.check({"tenders.json": feed(300), "today.json": {"n": {"open": 999}}}, {}))


class Reuse(unittest.TestCase):
    def test_active_sources_state_reuse_with_evidence(self):
        reg = json.load(open(os.path.join(os.path.dirname(__file__), "..", "tools", "sources", "registry.json"), encoding="utf8"))
        for s in reg:
            if s["collect"] != "PASS": continue
            self.assertIn(s.get("reuse"), ("PASS", "FAIL", "UNKNOWN"), s["id"])
            self.assertTrue(s.get("reuse_url", "").startswith("http"), s["id"] + " needs a terms link")
            self.assertTrue(s.get("reuse_checked"), s["id"])


class ContractsFinderRecord(unittest.TestCase):
    PKG = json.dumps({"releases": [{"id": "de6f4b86-1352-4c39-9b37-199113e189da-920130", "ocid": "ocds-b5fd17-17d4acd2-34d6-4bbc-adce-12b741b20fd4",
                                    "tender": {"title": "CA18606 - York College", "tenderPeriod": {"endDate": "2026-11-27T17:00:00Z"}}, "buyer": {"name": "York College"}}]})
    X = {"source": "UK Contracts Finder", "sid": "ocds-b5fd17-17d4acd2-34d6-4bbc-adce-12b741b20fd4",
         "url": "https://www.contractsfinder.service.gov.uk/Notice/de6f4b86-1352-4c39-9b37-199113e189da"}

    def setUp(self):
        import verify_samples as VS; self.VS = VS; self.orig = VS.http; import time; self.sleep = time.sleep; time.sleep = lambda s: None

    def tearDown(self):
        self.VS.http = self.orig; import time; time.sleep = self.sleep

    def fake(self, answers):
        calls = []
        def h(url, *a, **k):
            calls.append(url); st, body = answers[len(calls) - 1]; self.VS.TRACE.append({"url": url, "status": st, "type": "application/json" if body.startswith("{") else "text/html"}); return st, body
        self.VS.http = h; return calls

    def test_release_package_matches(self):
        calls = self.fake([(200, self.PKG)])
        self.assertEqual(self.VS.official(self.X), ("CA18606 - York College", "2026-11-27", "York College"))
        self.assertTrue(calls[0].endswith("/Published/Notice/releases/de6f4b86-1352-4c39-9b37-199113e189da.json"))

    def test_html_error_page_falls_back_to_records_then_unknown(self):
        calls = self.fake([(200, "<html>If you typed the web address, check it is correct</html>"), (404, "")])
        self.assertEqual(self.VS.official(self.X)[0], "UNAVAILABLE")          # never a match, never a mismatch
        self.assertTrue(calls[1].endswith("/Published/Notice/records/ocds-b5fd17-17d4acd2-34d6-4bbc-adce-12b741b20fd4.json"))

    def test_records_fallback_can_confirm(self):
        rec = json.dumps({"records": [{"compiledRelease": json.loads(self.PKG)["releases"][0]}]})
        self.fake([(404, ""), (200, rec)])
        self.assertEqual(self.VS.official(self.X)[1], "2026-11-27")

    def test_rate_limit_is_unknown(self):
        self.fake([(429, ""), (429, "")])
        self.assertEqual(self.VS.official(self.X)[0], "UNAVAILABLE")


class OpenCatalogue(unittest.TestCase):
    """Notices missing from today's search are re-read by id (ChatGPT PR #12 reviews §3 and 297ba85 §2)."""
    NOW = datetime.datetime(2026, 11, 20, 0, 0, tzinfo=datetime.timezone.utc); STAMP = "2026-11-20T00:00Z"

    def prev(self, **kw):
        x = {"source": "UK Contracts Finder", "sid": "ocds-1", "url": "https://cf/1", "title": "Catering tender", "deadline": "2026-12-02",
             "deadline_at": "2026-12-02T17:00:00Z", "added": "2026-11-10", "iso": "GB", "buyer": "Trust"}
        x.update(kw); return {x["url"]: x}

    @staticmethod
    def rec(status="active", dl="2026-12-02T17:00:00Z", title="Catering tender", ok=True, why=""):
        import verify_samples as VS
        return {"ok": ok, "id": "ocds-1", "title": title, "deadline_at": dl, "timed": "T" in dl, "status": VS.norm_status(status),
                "status_raw": status, "buyer": "Trust", "checked_at": "2026-11-20T00:00Z", "why": why}

    def run_(self, prev, state="EMPTY_SUCCESS", got=(), lookup=None, budget=40, src="UK Contracts Finder", now=None):
        return FT.carry(src, list(got), state, prev, now or self.NOW, self.STAMP, lookup or (lambda x: self.rec(ok=False, why="HTTP 200, not OCDS JSON")), [budget])

    def test_active_old_but_open_notice_is_kept_with_full_grade(self):
        out, c = self.run_(self.prev(), lookup=lambda x: self.rec())
        self.assertEqual(out[0]["verify"], "full"); self.assertNotIn("stale", out[0]); self.assertEqual(out[0]["added"], "2026-11-10")
        self.assertEqual(out[0]["last_verified_at"], "2026-11-20T00:00Z"); self.assertEqual(c["carried_verified"], 1)

    def test_same_day_deadline_moved_earlier_is_applied(self):
        out, _ = self.run_(self.prev(), lookup=lambda x: self.rec(dl="2026-12-02T10:00:00Z"))
        self.assertEqual(out[0]["deadline_at"], "2026-12-02T10:00:00Z")
        # and if the earlier time has already passed, the notice is dropped instead of showing open until 17:00
        late = datetime.datetime(2026, 12, 2, 12, 0, tzinfo=datetime.timezone.utc)
        out, c = self.run_(self.prev(), lookup=lambda x: self.rec(dl="2026-12-02T10:00:00Z"), now=late)
        self.assertEqual(out, []); self.assertEqual(c["dropped_closed"], 1)

    def test_same_day_deadline_moved_later_is_applied(self):
        out, _ = self.run_(self.prev(), lookup=lambda x: self.rec(dl="2026-12-02T23:00:00+01:00"))
        self.assertEqual(out[0]["deadline_at"], "2026-12-02T23:00:00+01:00")

    def test_cancelled_withdrawn_or_closed_at_publisher_is_dropped(self):
        for st in ("cancelled", "withdrawn", "unsuccessful", "complete"):
            out, c = self.run_(self.prev(), lookup=lambda x, st=st: self.rec(status=st))
            self.assertEqual(out, [], st); self.assertEqual(c["dropped_cancelled"], 1, st)

    def test_status_not_given_is_never_confirmed_open(self):
        out, c = self.run_(self.prev(source="EU TED"), src="EU TED", lookup=lambda x: self.rec(status=None))   # TED gives no status
        self.assertTrue(out[0]["stale"]); self.assertEqual(out[0]["verify"], "partial"); self.assertEqual(c["carried_verified"], 0)

    def test_world_bank_date_without_zone_is_date_grade(self):
        out, _ = self.run_(self.prev(source="World Bank", deadline_at="2026-12-02"), src="World Bank", lookup=lambda x: self.rec(status="Published", dl="2026-12-02"))
        self.assertEqual(out[0]["verify"], "date"); self.assertEqual(out[0]["deadline_at"], "2026-12-02")

    def test_unconfirmable_is_stale_and_keeps_real_last_check(self):
        out, c = self.run_(self.prev())
        self.assertTrue(out[0]["stale"]); self.assertEqual(out[0]["stale_since"], self.STAMP)
        self.assertEqual(out[0]["last_verified_at"], "")                       # NOT the first-seen date
        out, _ = self.run_(self.prev(last_verified_at="2026-11-18T06:10Z"))
        self.assertEqual(out[0]["last_verified_at"], "2026-11-18T06:10Z")
        import deadline as DL
        self.assertFalse(DL.is_listed_open(out[0], self.NOW))

    def test_title_mismatch_and_rate_limit_are_not_confirmations(self):
        out, _ = self.run_(self.prev(), lookup=lambda x: self.rec(title="Something else"))
        self.assertTrue(out[0]["stale"])
        out, _ = self.run_(self.prev(), lookup=lambda x: self.rec(ok=False, why="rate limited (429)"))
        self.assertTrue(out[0]["stale"])

    def test_stale_dropped_after_48_hours(self):
        out, c = self.run_(self.prev(stale=True, stale_since="2026-11-17T23:00Z"))
        self.assertEqual(out, []); self.assertEqual(c["dropped_unverified"], 1)
        out, c = self.run_(self.prev(stale=True, stale_since="2026-11-18T01:00Z"))
        self.assertEqual(len(out), 1)

    def test_closed_notice_never_carried(self):
        out, c = self.run_(self.prev(deadline="2026-11-19", deadline_at="2026-11-19T12:00:00Z"))
        self.assertEqual(out, []); self.assertEqual(c["dropped_closed"], 1)

    def test_notice_in_todays_search_is_not_duplicated(self):
        p = self.prev(); out, _ = self.run_(p, state="SUCCESS", got=[dict(list(p.values())[0])])
        self.assertEqual(out, [])

    def test_success_of_unwindowed_source_does_not_carry(self):
        out, _ = self.run_(self.prev(source="EU TED"), state="SUCCESS", src="EU TED")
        self.assertEqual(out, [])

    def test_lookup_budget(self):
        p = {}
        for i in range(3): p.update(self.prev(sid=f"ocds-{i}", url=f"https://cf/{i}"))
        out, c = self.run_(p, lookup=lambda x: self.rec(), budget=1)
        self.assertEqual((c["verify_lookups"], c["carried_verified"], c["carried_stale"]), (1, 1, 2))


class AllSourcesEmpty(unittest.TestCase):
    """Fallback when every source returns nothing: only VALID notices come back, and only as stale."""
    def test_valid_restored_as_stale_invalid_and_closed_not_restored(self):
        now = datetime.datetime.now(datetime.timezone.utc); stamp = now.strftime("%Y-%m-%dT%H:%MZ")
        ok = item(sid="A", url="https://x/a"); ok["last_verified_at"] = "2026-11-16T11:14Z"
        closed = item(sid="B", url="https://x/b", deadline=(now.date() - datetime.timedelta(days=2)).isoformat())
        closed["deadline_at"] = closed["deadline"]
        bad = item(sid="C", url="https://x/c", deadline="2026-02-31"); bad["deadline_at"] = "2026-02-31"
        notitle = item(sid="D", url="https://x/d", title="")
        out = FT.all_empty_fallback({x["url"]: x for x in (ok, closed, bad, notitle)}, now, stamp)
        self.assertEqual([x["sid"] for x in out], ["A"])
        self.assertTrue(out[0]["stale"]); self.assertEqual(out[0]["last_verified_at"], "2026-11-16T11:14Z")
        import deadline as DL
        self.assertFalse(DL.is_listed_open(out[0], now))


class OfficialRecord(unittest.TestCase):
    def test_status_mapping(self):
        import verify_samples as VS
        for raw, want in [("active", "ACTIVE"), ("active.tendering", "ACTIVE"), ("Published", "ACTIVE"), ("cancelled", "CANCELLED"),
                          ("withdrawn", "CANCELLED"), ("unsuccessful", "CLOSED"), ("complete", "CLOSED"), (None, "UNKNOWN"), ("planned", "UNKNOWN")]:
            self.assertEqual(VS.norm_status(raw), want, raw)

    def test_sample_listing_a_cancelled_notice_fails(self):
        import verify_samples as VS
        r = VS.judge({"url_status": 200, "official_status": "CANCELLED", "record_unavailable": False, "title_ok": True, "deadline_ok": True})
        self.assertEqual(r["verdict"], "FAIL")

    def test_ted_exact_deadline(self):
        self.assertEqual(FM.ted_deadline(["2026-11-16+01:00", "2026-11-15+01:00"], ["17:00:00+01:00", "09:30:00+01:00"]), "2026-11-15T09:30:00+01:00")
        self.assertEqual(FM.ted_deadline(["2026-11-16+01:00"], []), "2026-11-16+01:00")
        self.assertEqual(FM.ted_deadline(["2026-11-16+01:00"], ["17:00+01:00"]), "2026-11-16T17:00:00+01:00")
