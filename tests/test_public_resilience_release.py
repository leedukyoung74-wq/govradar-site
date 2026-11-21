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
    def read(self,n): return ("new 106.4L release "+sentinel.SAFE_STOVE["ko"]).encode("utf-8")
class TestPublicVersionSentinel(TestCase):
    def test_successful_release_text(self):
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=MockResponse()) as request:
            result=sentinel.check("https://radar.wmm-hoa.com/ko/prepare/","106.4L")
            self.assertTrue(result["ready"])
            self.assertEqual(request.call_args.args[0].get_method(),"GET")
    def test_old_unsafe_indoor_stove_copy_blocks(self):
        class UnsafeStoveResponse(MockResponse):
            def read(self,n):
                return ("106.4L "+sentinel.SAFE_STOVE["ko"]+
                        " "+sentinel.OLD_UNSAFE["ko"]).encode("utf-8")
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=UnsafeStoveResponse()):
            result=sentinel.check("https://radar.wmm-hoa.com/ko/prepare/","106.4L")
            self.assertFalse(result["ready"])
            self.assertFalse(result["stove_safety_verified"])
    def test_missing_review_noindex_blocks(self):
        class UnprotectedResponse(MockResponse):
            def read(self,n): return b"wmm-resilience demo without noindex"
        with mock.patch.object(sentinel.urllib.request,"urlopen",return_value=UnprotectedResponse()):
            result=sentinel.check("https://radar.wmm-hoa.com/en/resilience/","wmm-resilience")
            self.assertFalse(result["ready"])
            self.assertFalse(result["review_not_indexed"])
    def test_all_locales_have_safe_outdoor_stove_text(self):
        self.assertEqual(set(sentinel.SAFE_STOVE),set(sentinel.LANGS))
        self.assertEqual(set(sentinel.OLD_UNSAFE),set(sentinel.LANGS))
        for language in sentinel.LANGS:
            self.assertTrue(sentinel.SAFE_STOVE[language])
            self.assertTrue(sentinel.OLD_UNSAFE[language])
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
    def test_public_blackout_panel_safe_stove_copy_all_seven_languages(self):
        # The separate stockpile cards were already safe; the global quick panel
        # was still offering unsafe "ventilate indoors" advice. Protect both.
        import ast
        import json
        content=json.loads((ROOT/"src/content.json").read_text(encoding="utf8"))
        row=next(x for x in content["prep"]["scenarios"] if x["id"]=="blackout")
        self.assertEqual(len(row["ko_items"]),8)
        self.assertEqual(len(row["en_items"]),8)
        for lang in ("ko","en"):
            self.assertNotIn(sentinel.OLD_UNSAFE[lang], row[lang+"_items"][2])
            self.assertIn(sentinel.SAFE_STOVE[lang],row[lang+"_items"][2])
        src=(ROOT/"build.py").read_text(encoding="utf8")
        tree=ast.parse(src,filename="build.py")
        assigns=[n for n in tree.body if isinstance(n,ast.Assign) and
                 any(isinstance(t,ast.Name) and t.id=="STOVE_SAFE_BY_LANG" for t in n.targets)]
        self.assertEqual(len(assigns),1)
        translations=ast.literal_eval(assigns[0].value)
        self.assertEqual(set(translations),set(sentinel.LANGS))
        for lang in sentinel.LANGS:
            self.assertIn(sentinel.SAFE_STOVE[lang], translations[lang])
            self.assertNotIn(sentinel.OLD_UNSAFE[lang],translations[lang])
        self.assertIn("_safe_prep_item(L, x, j, item)",src)
        self.assertEqual(row["ko_items"].index(row["ko_items"][2]),2)

    def test_no_token_or_deploy_endpoint(self):
        source=(ROOT/"tools/verify_public_resilience_release.py").read_text(encoding="utf8")
        for prohibited in ("CLOUDFLARE_API_TOKEN","POST","PUT","DELETE","wrangler pages deploy"):
            self.assertNotIn(prohibited,source)
