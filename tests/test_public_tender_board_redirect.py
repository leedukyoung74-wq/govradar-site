"""GOV RADAR /mdb direct public route: map-first still applies to unrelated non-member pages."""
import pathlib
import re
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PublicTenderBoardGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = (ROOT / "build.py").read_text(encoding="utf-8")
        m = re.search(r'_GATE = r"""(.*?)"""', src, re.S)
        assert m, "map-first gate missing"
        cls.gate = m.group(1).removeprefix("<script>").removesuffix("</script>")

    def test_public_tender_board_is_exempted(self):
        self.assertIn(r"(legal|member|pay|mdb)", self.gate)

    def test_mdb_direct_access_and_home_map_first(self):
        if not shutil.which("node"):
            self.skipTest("Node not installed")
        import json
        for path, expect in [("/ko/mdb/","NO_REDIRECT"),("/en/mdb/","NO_REDIRECT"),
                             ("/ko/about/","/map/"),("/ar/about/","/map/ar/")]:
            with self.subTest(path=path):
                js = f"""
                const location={{search:'',hash:'',pathname:{json.dumps(path)},replace:(x)=>process.stdout.write(x)}};
                const document={{documentElement:{{lang:{json.dumps(path.split('/')[1])}}}}};
                const localStorage={{getItem:()=>null}};
                {self.gate}
                """
                r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(r.stdout or "NO_REDIRECT",expect)


if __name__ == "__main__":
    unittest.main()
