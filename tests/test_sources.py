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
             "buyer-country": ["FRA"], "deadline-receipt-tender-date-lot": [today + "+14:00"], "contract-nature": ["works"],
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
        self.assertEqual(st["failed"], 0); self.assertEqual(FT.classify_state(st), "SUCCESS")
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
