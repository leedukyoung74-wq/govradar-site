"""Offline tests: static route allowlist and strictly read-only request method."""
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from ops import live_routes_readonly as L

class RouteProbe(unittest.TestCase):
    def test_only_seven_home_and_three_actual_forms(self):
        self.assertEqual(len(L.routes()),10)
        self.assertEqual(L.routes()[:7],tuple(f"/{x}/" for x in L.LANGS))
        self.assertEqual(L.routes()[7:],("/ko/request/","/en/request/","/ar/request/"))
    def test_no_form_send_or_offsite_paths(self):
        seen=[]
        class O:
            def open(self,request,timeout):
                seen.append(request)
                raise HTTPError(request.full_url,404,"not found",{},None)
        result=L.fetch_status("/ko/",opener=O())
        self.assertEqual(result["status"],404)
        self.assertEqual(seen[0].get_method(),"GET")
        self.assertNotIn("Authorization",seen[0].headers)
        with self.assertRaises(ValueError):
            L.fetch_status("/ko/request/?email=secret",opener=O())
    def test_no_pass_for_html_redirect_or_http_error(self):
        good=[{"path":p,"status":200,"content_type":"text/html"} for p in L.routes()]
        self.assertEqual(L.interpret(good)["result"],"PASS")
        good[0]["status"]=302
        self.assertEqual(L.interpret(good)["result"],"DEGRADED")
        self.assertFalse(L.interpret(good)["mobile_rendering_verified"])
        self.assertFalse(L.interpret(good)["form_submission_verified"])
