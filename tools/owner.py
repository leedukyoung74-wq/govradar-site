"""Owner-only full view of GOV RADAR.
Builds a JSON snapshot of everything (open/new/imminent tenders, past tenders by recurring field with
feasibility checklists, stale countries, regions, scheduled-task status, running costs) and encrypts it
with a key derived from the owner code only (members cannot decrypt it). Output: data_branch/m/o.json.
The owner code is also registered as a member (exp 2099) so every locked item on the site opens too.
Usage: python3 tools/owner.py [code]   -> prints the owner link"""
import base64, datetime, glob, json, os, secrets, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
import member as M, pages3 as P3
ITER = 150000; b64 = lambda b: base64.b64encode(b).decode()
TODAY = datetime.date.today().isoformat()
NAMES = json.load(open(os.path.join(ROOT, "src", "names.json"), encoding="utf8"))
KON = json.load(open(os.path.join(ROOT, "src", "ko_names.json"), encoding="utf8"))
REGS = json.load(open(os.path.join(ROOT, "src", "regions.json"), encoding="utf8"))
TASKS = os.path.join(ROOT, "private", "tasks.json")

def load():
    D = {}
    for f in glob.glob(os.path.join(ROOT, "export", "countries", "*.json")):
        j = json.load(open(f, encoding="utf8")); D[os.path.basename(f)[:2]] = j.get("data", j)
    return D

def snapshot():
    D = load(); nm = lambda i: (NAMES.get(i) or {}).get("ko", i)
    op = P3.all_tenders(D, {i: {} for i in D}, TODAY)
    def tr(x):
        t = x["t"]; dl = x["dl"]; dd = (datetime.date.fromisoformat(dl) - datetime.date.fromisoformat(TODAY)).days
        return {"iso": x["iso"], "c": nm(x["iso"]), "ko": KON.get(t.get("title", ""), t.get("title", "")), "orig": t.get("title", ""),
                "buyer": KON.get(t.get("buyer", ""), t.get("buyer", "")), "dl": dl, "d": dd, "new": bool(x.get("new")), "hot": dd <= 15,
                "src": t.get("source", ""), "url": t.get("url", ""), "sec": x["sec"]}
    names = {k: nk for k, nk, *_ in P3.SECT}; names["other"] = "기타"
    C = {"DATA": D, "TODAY": TODAY}
    past = [{"sec": names.get(k, k), "n": len(xs), "countries": sorted({nm(x["iso"]) for x in xs}), "multi": len({x["iso"] for x in xs}) >= 2,
             "prep": P3.prep_list(k, "ko"),
             "items": [{"dl": x["dl"], "c": nm(x["iso"]), "ko": KON.get(x["t"].get("title", ""), x["t"].get("title", "")), "url": x["t"].get("url", "")} for x in xs]}
            for k, xs in P3.past_groups(C)]
    done = [i for i, d in D.items() if d.get("agenda")]
    stale = sorted(({"c": nm(i), "iso": i, "u": str(D[i].get("updated") or "")} for i in done), key=lambda x: x["u"])[:40]
    rdone = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "export", "regions", "*.json"))}
    regs = [{"ko": r["ko"], "p": nm(r["parent"]), "done": r["iso"] in rdone} for r in REGS]
    tasks = json.load(open(TASKS, encoding="utf8")) if os.path.exists(TASKS) else []
    return {"at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sum": {"countries": len(done), "regions": sum(r["done"] for r in regs), "open": len(op), "new": sum(1 for x in op if x.get("new")),
                    "hot": sum(1 for x in op if (datetime.date.fromisoformat(x["dl"]) - datetime.date.fromisoformat(TODAY)).days <= 15),
                    "past": sum(p["n"] for p in past), "biz": sum(len(d.get("biz") or []) for d in D.values())},
            "open": [tr(x) for x in op], "past": past, "stale": stale, "regions": regs, "tasks": tasks}

def owner_code(code=None):
    m = M._members(); e = "owner@govradar.local"
    if code: pass
    elif e in m: code = m[e]["code"]
    else: code = "-".join(secrets.token_hex(2).upper() for _ in range(6))
    m[e] = {"code": code, "exp": "2099-12-31", "added": m.get(e, {}).get("added", TODAY), "owner": True}
    M._save_members(m); M.write_keys(); return code

def main():
    code = owner_code(sys.argv[1] if len(sys.argv) > 1 else None)
    salt = secrets.token_bytes(16); iv = secrets.token_bytes(12)
    k = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(("owner:" + code).encode())
    ct = AESGCM(k).encrypt(iv, json.dumps(snapshot(), ensure_ascii=False).encode(), None)
    os.makedirs(os.path.join(M.OUT, "m"), exist_ok=True)
    json.dump({"v": 1, "iter": ITER, "s": b64(salt), "iv": b64(iv), "c": b64(ct)}, open(os.path.join(M.OUT, "m", "o.json"), "w"))
    print("owner link: https://radar.wmm-hoa.com/owner/#" + code)

if __name__ == "__main__": main()
