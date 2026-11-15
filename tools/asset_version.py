#!/usr/bin/env python3
"""Add ?v=<content hash> to code assets referenced from every HTML page in the publish folder,
so browsers never keep an old site.css / site.js / gvhdr.js after an update (assets are cached 7 days)."""
import hashlib, os, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else "cf/public"
names = ["site.css", "site.js", "gvhdr.js", "hotmap.js", "auth.js", "config.js"]
ver = {}
for n in names:
    p = os.path.join(root, "assets", n)
    if os.path.exists(p): ver[n] = hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
pat = re.compile(r'(/assets/(' + "|".join(re.escape(n) for n in ver) + r'))(\?v=[0-9a-f]+)?(?=["\'])')
cnt = 0
for d, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith(".html"): continue
        p = os.path.join(d, f); s = open(p, encoding="utf-8").read()
        t = pat.sub(lambda m: m.group(1) + "?v=" + ver[m.group(2)], s)
        if t != s: open(p, "w", encoding="utf-8").write(t); cnt += 1
print("asset versions", ver, "pages", cnt)
