"""dist/ -> cf/public/ : Cloudflare Pages용 사본 (신청서·회원가입은 Netlify로 중계)"""
import re, shutil, pathlib, sys
SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
DST = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "cf/public")
if DST.exists(): shutil.rmtree(DST)
shutil.copytree(SRC, DST)
EXTRA = pathlib.Path(__file__).resolve().parent.parent / "cf" / "extra"
if EXTRA.exists(): shutil.copytree(EXTRA, DST, dirs_exist_ok=True)
FORM = re.compile(r'(<form\b[^>]*data-netlify="true"[^>]*?)action="(/[^"]*)"')
n = 0
for f in DST.rglob("*.html"):
    t = f.read_text("utf-8")
    t2, k = FORM.subn(lambda m: m.group(1) + 'action="/nfform?next=' + m.group(2) + '"', t)
    if k: f.write_text(t2, "utf-8"); n += k
a = DST / "assets" / "auth.js"
s = a.read_text("utf-8")
assert '"/.netlify/identity"' in s
a.write_text(s.replace('"/.netlify/identity"', '"/nfid"'), "utf-8")
print("forms rewritten:", n)
