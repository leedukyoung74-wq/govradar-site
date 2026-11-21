import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "live_prepbar_gate", ROOT / "ops/verify_live_prepbar_release_gate.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class Resp:
    def __init__(self, data, url, status=200):
        self.content = data.encode("utf-8")
        self.url = url
        self.status = status

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return self.content[:size]
    def geturl(self): return self.url


class LivePrepbarGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = pathlib.Path(self.tmp.name) / "baseline"
        self.patch = pathlib.Path(self.tmp.name) / "candidate"
        for lang, (unsafe, safe) in M.COPY.items():
            for root, phrase in ((self.base, unsafe), (self.patch, safe)):
                p = root / "public" / lang / "prepare" / "index.html"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(
                    '<html><link href="/a.css"><script src="/a.js"></script>'
                    + '<div class="pp" data-pp="blackout"><li>' + phrase + '</li></div>'
                    + '<h2>106.4L 이상</h2></html>', encoding="utf-8")

    def test_exactly_seven_languages_and_no_other_diff(self):
        rows = M.release_source_checks(self.base, self.patch)
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(x["pass"] for x in rows))

    def test_extra_script_or_html_injection_blocks(self):
        p = self.patch / "public" / "ko" / "prepare" / "index.html"
        p.write_text(p.read_text(encoding="utf8") + "<script>alert(1)</script>", encoding="utf8")
        rows = M.release_source_checks(self.base, self.patch)
        self.assertEqual(sum(x["pass"] for x in rows), 6)
        self.assertFalse(rows[0]["checks"]["only_one_list_item_modified"])

    def test_missing_language_blocks(self):
        (self.patch / "public" / "ar" / "prepare" / "index.html").unlink()
        rows = M.release_source_checks(self.base, self.patch)
        self.assertFalse(next(x for x in rows if x["lang"] == "ar")["pass"])

    def test_reintroduction_of_84l_blocks(self):
        p = self.patch / "public" / "en" / "prepare" / "index.html"
        p.write_text(p.read_text(encoding="utf8").replace("106.4L", "84L"), encoding="utf8")
        self.assertFalse(next(x for x in M.release_source_checks(self.base,self.patch) if x["lang"] == "en")["pass"])

    def test_no_network_by_default(self):
        with mock.patch.object(M.urllib.request, "urlopen", side_effect=AssertionError("NO NETWORK")):
            out = M.run(self.base, self.patch)
        self.assertTrue(out["release_patch_source_ok"])
        self.assertFalse(out["release_production_confirmed"])
        self.assertEqual(out["public_patch_visible_total"], 0)
        self.assertEqual(out["readiness"], "PREVIEW_REQUIRED")

    def test_live_get_cannot_imply_safe_with_obsolete_text(self):
        url = "https://radar.wmm-hoa.com/ko/prepare/"
        body = '<li>'+M.COPY["ko"][0]+'</li><b>106.4L</b>'
        def fake(req, timeout):
            self.assertEqual(req.get_method(),"GET")
            self.assertEqual(req.full_url,url)
            return Resp(body, url)
        out = M.http_probe_one("https://radar.wmm-hoa.com", "ko", opener=fake)
        self.assertEqual(out["release_state"], "OLD_UNSAFE_COPY_VISIBLE")
        self.assertTrue(out["unsafe_copy_present"])

    def test_candidate_visible_from_official_host_only(self):
        url = "https://radar.wmm-hoa.com/en/prepare/"
        body = '<li>'+M.COPY["en"][1]+'</li><b>106.4L</b>'
        out = M.http_probe_one("https://radar.wmm-hoa.com","en",
                               opener=lambda req, timeout: Resp(body,url))
        self.assertEqual(out["release_state"],"SAFE_PATCH_VISIBLE")
        out = M.http_probe_one("https://radar.wmm-hoa.com","en",
                               opener=lambda req, timeout: Resp(body,"https://wrong.example.com/"))
        self.assertEqual(out["release_state"],"UNVERIFIED")

    def test_server_failures_do_not_count_as_safe(self):
        url = "https://wmm-radar.pages.dev/fr/prepare/"
        out = M.http_probe_one("https://wmm-radar.pages.dev", "fr",
            opener=lambda req,timeout: Resp("",url,status=503))
        self.assertNotEqual(out["release_state"], "SAFE_PATCH_VISIBLE")


if __name__ == "__main__":
    unittest.main()
