"""Count the source registry and write tools/sources/SUMMARY.md, so the PR text can never drift from registry.json again.
Run: python tools/sources/summary.py   (tests/test_sources.py fails if SUMMARY.md is out of date)"""
import collections, json, os
HERE = os.path.dirname(os.path.abspath(__file__))

def counts(reg):
    c = collections.Counter(s["collect"] for s in reg)
    return {"total": len(reg), "PASS": c.get("PASS", 0), "FAIL": c.get("FAIL", 0), "UNKNOWN": c.get("UNKNOWN", 0),
            "by_kind": dict(sorted(collections.Counter(s["kind"] for s in reg).items()))}

def render(reg):
    c = counts(reg)
    lines = ["# Source registry summary (generated — do not edit by hand)", "",
             f"- Candidates: **{c['total']}** ({', '.join(f'{k} {v}' for k, v in c['by_kind'].items())})",
             f"- Collect status: **PASS {c['PASS']} / FAIL {c['FAIL']} / UNKNOWN {c['UNKNOWN']}**",
             "- PASS = a collector has actually returned notices from this source. Candidates are not live connections.", "",
             "| Status | ID | Source | Note |", "|---|---|---|---|"]
    for s in sorted(reg, key=lambda s: ({"PASS": 0, "FAIL": 1}.get(s["collect"], 2), s["id"])):
        if s["collect"] in ("PASS", "FAIL"):
            lines.append(f"| {s['collect']} | {s['id']} | {s['name']} | {s.get('note', '').replace('|', '/')} |")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    reg = json.load(open(os.path.join(HERE, "registry.json"), encoding="utf8"))
    open(os.path.join(HERE, "SUMMARY.md"), "w", encoding="utf8").write(render(reg)); print(counts(reg))
