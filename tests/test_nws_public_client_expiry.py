"""Protect public NWS 'active warning' UI from already-expired source records.

This is an offline Node vm test of the actual shipped browser JavaScript.
No network calls, real user data, or website deployment.
"""
import json
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS_FILE = ROOT / "cf" / "extra" / "assets" / "wmm-official-sources.js"


class NwsPublicClientExpiryTests(unittest.TestCase):
    def test_client_date_and_warning_expiry_logic(self):
        if shutil.which("node") is None:
            self.skipTest("Node.js not available on test host")
        script = r"""
const fs=require('fs'),vm=require('vm');
let src=fs.readFileSync(process.argv[1], 'utf8');
const marker='  function createPanel(type) {';
if(!src.includes(marker))throw Error('missing browser panel insertion marker');
src=src.replace(marker, '  globalThis.__test={safeFresh:safeFresh,activeNwsItem:activeNwsItem};\n'+marker);
const ctx={
  document:{documentElement:{lang:'en'},readyState:'loading',addEventListener:function(){}},
  location:{pathname:'/cyber'},
  URL:URL
};
vm.runInNewContext(src,ctx,{timeout:1000});
if(!ctx.__test)throw Error('missing test hooks');
const t=ctx.__test,now=Date.now();
const h=(minutes)=>({ok:true,stale:false,last_ok:new Date(now-minutes*60000).toISOString()});
const warning=(issued,expires)=>({issued_at:new Date(now+issued*60000).toISOString(),ends_at:new Date(now+expires*60000).toISOString()});
const checks={
 freshNws:t.safeFresh(h(10),'nws')===true,
 oldSnapshotStale:t.safeFresh(h(80),'nws')===false,
 farFutureNotFresh:t.safeFresh(h(-80),'nws')===false,
 fiveMinuteSkewAllowed:t.safeFresh(h(-2),'nws')===true,
 explicitlyStaleNotFresh:t.safeFresh({...h(3),stale:true},'nws')===false,
 expiredWarningNotActive:t.activeNwsItem(warning(-30,-1),now)===false,
 validWarningActive:t.activeNwsItem(warning(-30,30),now)===true,
 futureIssuedWarningBlocked:t.activeNwsItem(warning(40,50),now)===false,
 missingExpiryBlocked:t.activeNwsItem({issued_at:new Date(now-60000).toISOString()},now)===false,
 malformedExpiryBlocked:t.activeNwsItem({issued_at:'bad',ends_at:'bad'},now)===false
};
console.log(JSON.stringify(checks));
if(Object.values(checks).some(v=>!v))process.exit(1);
"""
        result = subprocess.run(
            ["node", "-e", script, str(JS_FILE)],
            capture_output=True, text=True, timeout=5, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertTrue(all(json.loads(result.stdout).values()))

    def test_no_active_alert_list_when_feed_stale(self):
        source = JS_FILE.read_text(encoding="utf-8")
        self.assertIn('if(type==="nws" && !okay)', source)
        self.assertIn('n.list.appendChild(el("li","",I.unavailable));return;', source)
        self.assertIn('activeNwsItem(item,Date.now())', source)
        self.assertIn('nwsLive', source)
        self.assertIn('},60*1000);', source)
        self.assertIn('},10*60*1000);', source)
        self.assertNotIn('Math.abs(Date.now()-d.getTime())', source)


if __name__ == "__main__":
    unittest.main()
