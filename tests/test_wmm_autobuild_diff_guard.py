"""Review-only guard: validate AI-generated source changes before any branch push."""
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from wmm_autobuild_diff_guard import names_in_patch, allowed, MAX_FILES

def patch_for(name):
    return ('diff --git a/'+name+' b/'+name+'\n'
            '--- a/'+name+'\n+++ b/'+name+'\n'
            '@@ -1 +1 @@\n-old\n+new\n').encode()

class AutobuildPatchGuardTests(unittest.TestCase):
    def test_govradar_feature_paths_allowed(self):
        for name in ("build.py","pages3.py","web/mdb.js","tests/test_x.py",
                     "src/review_pages/quality.html","docs/x.md","schemas/x.json"):
            self.assertTrue(allowed(name),name)
            self.assertEqual(names_in_patch(patch_for(name)),[name])

    def test_sensitive_and_deploy_paths_blocked(self):
        for name in (".github/workflows/schedule.yml","private/secrets.json",
                     "cf/public/index.html","export/countries/KR.json",
                     "functions/api/ask.js","data/cty/KR.json",
                     "../out.txt","/tmp/out","-not-allowed"):
            self.assertFalse(allowed(name),name)

    def test_binary_and_symlink_patch_blocked(self):
        for text in (b"GIT binary patch",b"Binary files ",
                     b"new file mode 120000"):
            with self.assertRaises(ValueError):
                names_in_patch(patch_for("web/abc.js")+text+b"\n")

    def test_renames_and_copies_blocked(self):
        for line in ("rename from web/old.js","rename to web/new.js","copy from web/old.js"):
            with self.assertRaises(ValueError):
                names_in_patch(patch_for("web/abc.js")+line.encode()+b"\n")

    def test_empty_and_oversized_patch_blocked(self):
        with self.assertRaises(ValueError):
            names_in_patch(b"")
        with self.assertRaises(ValueError):
            names_in_patch(patch_for("build.py")+b"x"*260000)

    def test_files_count_limit(self):
        bulk=b"".join(patch_for("tests/test_%d.py"%i) for i in range(MAX_FILES+1))
        with self.assertRaises(ValueError):
            names_in_patch(bulk)

if __name__=="__main__":
    unittest.main()
