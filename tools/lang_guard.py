#!/usr/bin/env python3
"""Pages in es/fr/ar/vi/id whose body is still mostly English (content not yet translated) are replaced by a
redirect to the English page at the same path, so no screen mixes a translated menu with English body text."""
import os, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else "cf/public"
dry = "--dry" in sys.argv
EN = re.compile(r"\b(the|and|of|to|in|is|for|with|on|that|are|from|by|was|as|this|will|their)\b", re.I)
OWN = {"es": re.compile(r"\b(de|la|el|en|y|los|las|del|para|con|por|una|que|se|su|al)\b", re.I),
       "fr": re.compile(r"\b(de|la|le|les|des|et|en|du|pour|avec|une|que|est|sur|au|aux)\b", re.I),
       "id": re.compile(r"\b(dan|yang|di|untuk|dengan|ini|dari|pada|ke|tidak|atau|dalam|akan|oleh)\b", re.I),
       "vi": re.compile(r"\b(và|của|các|cho|trong|là|với|được|những|có|này|một|không|từ)\b", re.I),
       "ar": re.compile(r"(?:^|\s)(في|من|على|إلى|عن|مع|هذا|التي|الذي|أو|و\S+|ال\S+)", re.M)}
STRIP = re.compile(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<header.*?</header>|<select.*?</select>", re.S)
def share(html, L):
    """Share of text blocks (p, li, td, h3, h4, summary) that are English rather than language L."""
    body = STRIP.sub("", html)
    blocks = re.findall(r"<(?:p|li|td|h3|h4|summary|dd)\b[^>]*>(.*?)</(?:p|li|td|h3|h4|summary|dd)>", body, re.S)
    n = e = 0
    for b in blocks:
        t = re.sub(r"<[^>]+>", " ", b)
        en = len(EN.findall(t)); own = len(OWN[L].findall(t))
        if en + own < 2: continue
        n += 1
        if en > own: e += 1
    return e / n if n >= 8 else 0.0
FORCE = {"conflict", "mdb", "request"}
out = []
for L in OWN:
    base = os.path.join(root, L)
    for d, _, fs in os.walk(base):
        if "index.html" not in fs: continue
        p = os.path.join(d, "index.html"); rel = os.path.relpath(d, base)
        target = "/en/" + ("" if rel == "." else rel.replace(os.sep, "/") + "/")
        if not os.path.exists(os.path.join(root, "en", "" if rel == "." else rel, "index.html")): continue
        h = open(p, encoding="utf-8").read()
        if "http-equiv=\"refresh\"" in h: continue
        r = 1.0 if rel in FORCE else share(h, L)
        if r > 0.4:
            out.append((L, rel, round(r, 2)))
            if not dry:
                open(p, "w", encoding="utf-8").write(f'<!doctype html><html lang="{L}"><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={target}"><link rel="canonical" href="https://radar.wmm-hoa.com{target}"><script>location.replace("{target}"+location.search+location.hash)</script><a href="{target}">English</a></html>')
print("lang_guard:", len(out), "pages sent to English", "(dry run)" if dry else "")
for x in out[:400]: print(" ", *x)
