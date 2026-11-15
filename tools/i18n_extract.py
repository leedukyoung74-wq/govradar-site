"""Extract / apply translatable strings of a built English page (text nodes, a few attributes, JSON/JS string literals in inline scripts)."""
import re, html, json
TXT = re.compile(r'>([^<>]+)<')
ATT = re.compile(r'\b(alt|title|aria-label|placeholder|content)="([^"]*)"')
JSS = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
def want(t):
    t = t.strip()
    return len(t) > 1 and re.search(r'[A-Za-z]{2,}', t) and not re.match(r'^(https?:|/|#|data:|[\w.-]+\.(js|css|png|webp|jpg)$)', t) and not re.match(r'^[\w-]+$', t) or (t and ' ' in t and re.search(r'[A-Za-z]{3,}', t) and not t.startswith(('http', '/')))
def scripts(s): return [(m.start(1), m.end(1)) for m in re.finditer(r'<script[^>]*>(.*?)</script>', s, re.S)]
def segs(s):
    out = []
    sc = scripts(s); sty = [(m.start(1), m.end(1)) for m in re.finditer(r'<style[^>]*>(.*?)</style>', s, re.S)]
    inr = lambda p, R: any(a <= p < b for a, b in R)
    for m in TXT.finditer(s):
        if inr(m.start(1), sc) or inr(m.start(1), sty): continue
        out.append(("t", m.start(1), m.end(1), html.unescape(m.group(1))))
    for m in ATT.finditer(s):
        if m.group(1) == "content" and not re.search(r'name="(description|twitter:[a-z]+)"|property="og:(title|description)"', s[max(0, m.start()-80):m.start()]): continue
        out.append(("a", m.start(2), m.end(2), html.unescape(m.group(2))))
    for a, b in sc:
        for m in JSS.finditer(s, a, b):
            v = m.group(1)
            if ' ' in v and re.search(r'[A-Za-z]{3,}', v) and not re.search(r'[{};=]|function|\.(js|css)|https?:', v):
                try: out.append(("j", m.start(1), m.end(1), json.loads('"' + v + '"')))
                except Exception: pass
    return out
def core(t):
    m = re.match(r'^(\s*)(.*?)(\s*)$', t, re.S); return m.group(1), m.group(2), m.group(3)
def strings(s):
    seen = []
    for k, a, b, t in segs(s):
        _, c, _ = core(t)
        if c and want(c) and c not in seen: seen.append(c)
    return seen
def apply(s, tr):
    parts = []; last = 0
    for k, a, b, t in sorted(segs(s), key=lambda x: x[1]):
        if a < last: continue
        l, c, r = core(t)
        if c not in tr: continue
        v = l + tr[c] + r
        v = html.escape(v, quote=(k == "a")) if k != "j" else json.dumps(v, ensure_ascii=False)[1:-1]
        parts.append(s[last:a]); parts.append(v); last = b
    parts.append(s[last:]); return "".join(parts)
