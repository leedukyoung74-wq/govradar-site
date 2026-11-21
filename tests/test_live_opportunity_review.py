"""Mock only: no network, deployments, production data edits or customer notifications."""
import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("opps_gate",ROOT/"ops/verify_live_opportunity_review.py")
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

HTML_OLD='<!doctype html><a id="more">More</a><script>fetch("/data/opps.json");li.querySelector(".t").textContent=x.en;</script>'
HTML_NEW=('<!doctype html><a id="more">More</a><p id="source-disclaimer" role="note"></p>'
          '<script>fetch("/data/opps.json");'
          'const w={ko:"x",en:"x",es:"x",fr:"x",ar:"x",vi:"x",id:"x"};'
          'if(o.index_kind!=="unverified_country_brief_candidates"||o.verified_official_notice_count!==0'
          '||o.automated_customer_alerts_allowed!==false||'
          'o.items.some(x=>x.official_notice_verified!==false||x.may_send_business_alert!==false))return;'
          'li.querySelector(".t").textContent=x.en;'
          'x.official_notice_verified===true&&x.deadline?"";'
          '</script>')


class LiveOpportunityGateTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.old=pathlib.Path(temp.name)/"live"
        self.new=pathlib.Path(temp.name)/"candidate"
        row={"iso":"US","kind":"biz","slug":"united-states","ko":"Example","en":"Example","deadline":""}
        old={"updated":"2026-11-21","items":[row,row | {"iso":"KR"}]}
        new={**old,**M.SAFE_ROOT,"items":[x|M.SAFE_ROW for x in old["items"]]}
        for root,record,widget in ((self.old,old,HTML_OLD),(self.new,new,HTML_NEW)):
            path=root/M.INDEX_PATH;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(record,ensure_ascii=False),encoding="utf8")
            wp=root/M.WIDGET_PATH;wp.parent.mkdir(parents=True,exist_ok=True)
            wp.write_text(widget,encoding="utf8")

    def set_item(self,idx,field,value):
        path=self.new/M.INDEX_PATH
        data=json.loads(path.read_text(encoding="utf8"))
        data["items"][idx][field]=value
        path.write_text(json.dumps(data,ensure_ascii=False),encoding="utf8")

    def test_all_record_content_preserved_with_exact_flags(self):
        x=M.check_patch(self.old,self.new)
        self.assertTrue(x["pass"],x)
        self.assertEqual(x["record_count"],2)
        self.assertEqual(x["alert_eligible_count"],0)

    def test_modifying_original_title_blocks(self):
        self.set_item(0,"en","Fake mandatory government tender")
        x=M.check_patch(self.old,self.new)
        self.assertFalse(x["pass"])
        self.assertFalse(x["checks"]["each_original_item_preserved"])

    def test_injecting_unverified_source_url_blocks(self):
        self.set_item(0,"source_url","https://attacker.invalid/official")
        x=M.check_patch(self.old,self.new)
        self.assertFalse(x["pass"])
        self.assertFalse(x["checks"]["no_new_direct_sources_invented"])

    def test_booleans_cannot_be_numeric_zero(self):
        self.set_item(1,"official_notice_verified",0)
        x=M.check_patch(self.old,self.new)
        self.assertFalse(x["pass"])
        self.assertFalse(x["checks"]["each_item_qualified_unverified"])

    def test_missing_widget_warning_blocks(self):
        path=self.new/M.WIDGET_PATH
        path.write_text(HTML_OLD,encoding="utf8")
        x=M.check_patch(self.old,self.new)
        self.assertFalse(x["pass"])
        self.assertFalse(x["checks"]["visible_source_warning"])

    def test_no_network_until_explicit_probe(self):
        with mock.patch.object(M.urllib.request,"urlopen",side_effect=AssertionError("network forbidden")):
            out=M.run(self.old,self.new,probe=False)
        self.assertEqual(out["conclusion"],"PUBLIC_RELEASE_NOT_VERIFIED")
        self.assertFalse(out["public_policy_verified"])
        self.assertFalse(out["site_modified"])
        self.assertFalse(out["customer_alerts_sent"])

    def test_manual_probe_wrong_redirect_or_offline_never_proves_release(self):
        with mock.patch.object(M,"get_public",side_effect=ValueError("unreachable")):
            result=M.public_one(M.HOSTS[0])
        self.assertEqual(result["status"],"UNREACHABLE_OR_UNVERIFIABLE")
        self.assertTrue(result["http_check_failed"])

    def test_policy_changed_to_true_blocks(self):
        path=self.new/M.INDEX_PATH
        d=json.loads(path.read_text(encoding="utf8"))
        d["automated_customer_alerts_allowed"]=True
        path.write_text(json.dumps(d),encoding="utf8")
        self.assertFalse(M.check_patch(self.old,self.new)["pass"])


if __name__=="__main__":
    unittest.main()
