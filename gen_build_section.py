"""Builds the paste-ready 'GOV RADAR 구축 현황' section for wmm-hoa.com and gcsme.kr (ko/en)."""
import json, os, html
ROOT = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(ROOT, "src", "about.json"), encoding="utf8"))
BASE = "https://radar.wmm-hoa.com"
e = lambda s: html.escape(str(s), quote=True)
CSS = """<style>
@font-face{font-family:"WMM Nexon";font-weight:300;font-display:swap;src:local("NEXON Lv1 Gothic Light"),url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/NEXON%20Lv1%20Gothic%20OTF%20Light.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:400;font-display:swap;src:local("NEXON Lv1 Gothic"),url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/NEXON%20Lv1%20Gothic%20OTF.woff") format("woff")}
@font-face{font-family:"WMM Nexon";font-weight:700;font-display:swap;src:local("NEXON Lv1 Gothic Bold"),url("https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/NEXON%20Lv1%20Gothic%20OTF%20Bold.woff") format("woff")}
.grb{background:#0a0a0a;color:#f2f2ef;padding:80px 20px;font-family:"WMM Nexon","NEXON Lv1 Gothic","Apple SD Gothic Neo","Malgun Gothic",sans-serif;font-weight:400;word-break:keep-all}
.grb h2,.grb h4,.grb b,.grb .grb-btn,.grb em{font-weight:700}.grb p,.grb span{font-weight:400}.grb .grb-eb,.grb .grb-sh,.grb .grb-kpi span,.grb .grb-mods p,.grb .grb-road p,.grb .grb-foot span,.grb .grb-mods i{font-weight:300}
.grb *{box-sizing:border-box}.grb-in{max-width:1180px;margin:0 auto}
.grb-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:32px;align-items:end}
.grb-eb{font-size:12px;letter-spacing:.2em;opacity:.65;margin:0}
.grb-h{font-size:clamp(28px,4.2vw,46px);line-height:1.15;margin:12px 0 0;font-weight:700}
.grb-p{font-size:16px;line-height:1.75;opacity:.8;max-width:62ch;margin:16px 0 0}
.grb-cta{display:flex;gap:10px;flex-wrap:wrap}
.grb-btn{display:inline-block;padding:13px 22px;border-radius:8px;font-weight:700;text-decoration:none;border:1px solid #f2f2ef;color:#f2f2ef;white-space:nowrap}
.grb-btn.pri{background:#f2f2ef;color:#0a0a0a}
.grb-kpi{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid #f2f2ef;border-bottom:1px solid rgba(255,255,255,.18);margin:34px 0}
.grb-kpi div{padding:18px 16px;border-right:1px solid rgba(255,255,255,.18)}.grb-kpi div:last-child{border-right:0}
.grb-kpi b{display:block;font-size:34px;line-height:1.1}.grb-kpi span{font-size:12px;opacity:.65}
.grb-sh{font-size:12px;letter-spacing:.16em;opacity:.6;margin:36px 0 12px}
.grb-mods{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.18);border-radius:12px;overflow:hidden}
.grb-mods div{background:#111;padding:18px}.grb-mods i{font-style:normal;font-size:11px;opacity:.5;letter-spacing:.1em}
.grb-mods h4{margin:6px 0;font-size:16px;color:#f2f2ef}.grb-mods p{margin:0;font-size:13.5px;line-height:1.6;opacity:.7}
.grb-road{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}
.grb-road div{position:relative;padding:20px 16px 0 0;border-top:2px solid rgba(255,255,255,.25)}.grb-road div.on{border-top-color:#f2f2ef}
.grb-road div:before{content:"";position:absolute;top:-7px;left:0;width:12px;height:12px;border-radius:50%;background:#0a0a0a;border:2px solid rgba(255,255,255,.4)}
.grb-road div.on:before{background:#f2f2ef;border-color:#f2f2ef}
.grb-road em{font-style:normal;font-size:11px;font-weight:700;letter-spacing:.1em;opacity:.8}.grb-road h4{margin:4px 0;font-size:16px;color:#f2f2ef}.grb-road p{margin:0;font-size:13.5px;line-height:1.6;opacity:.7}
.grb-foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-top:30px;font-size:12px;opacity:.55}
@media (max-width:820px){.grb-top{grid-template-columns:1fr}.grb-kpi{grid-template-columns:1fr 1fr}.grb-kpi div:nth-child(2){border-right:0}.grb-kpi div:nth-child(-n+2){border-bottom:1px solid rgba(255,255,255,.18)}.grb-mods{grid-template-columns:1fr}.grb-road{grid-template-columns:1fr 1fr;row-gap:24px}}
</style>"""
def section(L, anchor="gov-radar-build"):
    a = A[L]; lp = "ko" if L == "ko" else "en"
    kpi = "".join(f"<div><b>{e(b)}</b><span>{e(s)}</span></div>" for b, s in a["kpi"])
    mods = "".join(f"<div><i>0{i+1}</i><h4>{e(h)}</h4><p>{e(p)}</p></div>" for i, (h, p) in enumerate(a["mods"]))
    road = "".join(f'<div class="{"on" if i < 3 else ""}"><em>{e(s)}</em><h4>{e(h)}</h4><p>{e(p)}</p></div>' for i, (s, h, p) in enumerate(a["road"]))
    return f"""<section class="grb" id="{anchor}"><div class="grb-in">
 <div class="grb-top"><div><p class="grb-eb">{e(a['eb'])}</p><h2 class="grb-h">{e(a['h'])}</h2><p class="grb-p">{e(a['lede'])}</p></div>
 <div class="grb-cta"><a class="grb-btn pri" href="{BASE}/{lp}/" target="_blank" rel="noopener">{e(a['cta'])}</a><a class="grb-btn" href="{BASE}/{lp}/#plans" target="_blank" rel="noopener">{e(a['cta2'])}</a></div></div>
 <div class="grb-kpi">{kpi}</div>
 <p class="grb-sh">{e(a['mods_h'])}</p><div class="grb-mods">{mods}</div>
 <p class="grb-sh">{e(a['road_h'])}</p><div class="grb-road">{road}</div>
 <div class="grb-foot"><span>{e(a['by'])}</span><span>{e(a['asof'])}</span></div>
</div></section>"""
def snippet(L, site):
    return f"<!-- GOV RADAR 구축 현황 section for {site} ({L}) — paste where the section should appear. Self-contained; class prefix grb- -->\n{CSS}\n{section(L)}\n"
if __name__ == "__main__":
    out = os.path.join(ROOT, "embeds")
    for L in ("ko", "en"):
        for site, fn in (("wmm-hoa.com", "wmm-hoa"), ("gcsme.kr", "gcsme")):
            sn = snippet(L, site)
            open(os.path.join(out, f"{fn}-build-{L}.html"), "w", encoding="utf8").write(sn)
            open(os.path.join(out, f"preview-{fn}-{L}.html"), "w", encoding="utf8").write(f'<!doctype html><html lang="{L}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>preview</title></head><body style="margin:0;font-family:system-ui,sans-serif">{sn}</body></html>')
    print("ok")
