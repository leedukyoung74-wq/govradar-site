"""Sentinel contracts: no write methods, explicit outdated legacy marker check."""
import importlib.util
from pathlib import Path
from unittest import TestCase, mock
import io

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("version_sentinel", ROOT/"tools/verify_public_resilience_release.py")
sentinel=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)

class MockResponse:
    status=200
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n): return b"new 106.4L release"
class TestPublicVersionSentinel(TestCase):
    def test_successful_release_text(self):
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=MockResponse()) as request:
            result=sentinel.check("https://radar.wmm-hoa.com/ko/prepare/","106.4L")
            self.assertTrue(result["ready"])
            self.assertEqual(request.call_args.args[0].get_method(),"GET")
    def test_stale_water_blocks(self):
        class OldResponse(MockResponse):
            def read(self,n): return b"old 84L and 106.4L mixed"
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=OldResponse()):
            result=sentinel.check("https://radar.wmm-hoa.com/ko/prepare/","106.4L")
            self.assertFalse(result["ready"])
            self.assertTrue(result["outdated_water_marker"])
    def test_routes_cover_all_locales_and_data_contract(self):
        self.assertEqual(len(sentinel.LANGS),7)
        self.assertEqual(len(sentinel.TESTS),22)
        for lang in sentinel.LANGS:
            self.assertIn((f"/{lang}/prepare/","106.4L"),sentinel.TESTS)
            self.assertIn((f"/{lang}/resilience/","wmm-resilience"),sentinel.TESTS)
        self.assertNotIn(("/quality/","Data Quality Review"),sentinel.TESTS)
    def test_false_product_verification_is_blocked(self):
        import json
        class FalseClaimResponse(MockResponse):
            def read(self,n):
                return json.dumps([{"iso":str(i),
                    "local_official_guidance_verified": i==0,
                    "retail_availability_verified":False,
                    "shelf_life_verified":False} for i in range(193)]).encode()
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=FalseClaimResponse()):
            state=sentinel.check("https://radar.wmm-hoa.com/data/wmm-food-country-profiles.json",'"local_official_guidance_verified"')
            self.assertEqual(state["product_claim_count"],1)
            self.assertFalse(state["ready"])
    def test_no_token_or_deploy_endpoint(self):
        source=(ROOT/"tools/verify_public_resilience_release.py").read_text(encoding="utf8")
        for prohibited in ("CLOUDFLARE_API_TOKEN","POST","PUT","DELETE","wrangler pages deploy"):
            self.assertNotIn(prohibited,source)
