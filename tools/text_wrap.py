#!/usr/bin/env python3
"""Korean line breaking for every page: break between words, never inside a Korean word (word-break: keep-all),
long URLs/codes still wrap (overflow-wrap), headings balanced, paragraphs without a lonely last word (text-wrap: pretty).
Adds the same block to web/site.css and, idempotently, to every static page under cf/extra (welcome, cyber, hazards, ...).
Korean only for keep-all: Chinese and Japanese have no spaces and must keep breaking between characters."""
import glob, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = (":lang(ko){word-break:keep-all;overflow-wrap:break-word}"
              "h1,h2,h3,h4,.lede{text-wrap:balance}"
       "p,li,dd,figcaption,blockquote{text-wrap:pretty}"
       ".code,pre,code{word-break:break-all;text-wrap:wrap}")
A, B = "/*kw:start*/", "/*kw:end*/"
n = 0
css = os.path.join(R, "web", "site.css"); t = open(css, encoding="utf-8").read()
if A in t: t = re.sub(re.escape(A) + r".*?" + re.escape(B), A + CSS + B, t, flags=re.S)
else: t = t.rstrip("\n") + "\n" + A + CSS + B + "\n"
open(css, "w", encoding="utf-8").write(t); n += 1
for f in glob.glob(os.path.join(R, "cf", "extra", "**", "*.html"), recursive=True):
    t = open(f, encoding="utf-8").read()
    if A in t: t2 = re.sub(re.escape(A) + r".*?" + re.escape(B), A + CSS + B, t, flags=re.S)
    elif "</head>" in t: t2 = t.replace("</head>", "<style>" + A + CSS + B + "</style></head>", 1)
    else: continue
    if t2 != t: open(f, "w", encoding="utf-8").write(t2); n += 1
print("updated", n)
