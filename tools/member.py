"""GOV RADAR analysis-member access (no server, no Netlify credits).

How it works
- One random master key K encrypts every member-only analysis file (AES-256-GCM).
- Each member gets a personal access code. keys.json holds, per member, K wrapped with a key
  derived from that code (PBKDF2-SHA256, 150k rounds) plus an expiry date. The site's browser
  code unwraps K with the member's code and decrypts the analysis files.
- Files are published on the GitHub "data" branch and read from raw.githubusercontent.com,
  so adding a member or refreshing analysis never needs a Netlify deploy.
- Revoke must rotate K and re-encrypt all current files in the same guarded local operation. Published data branch and prior downloads remain separate.

Usage
  python3 tools/member.py encrypt                 # encrypt private/m/** into data/m/**
  python3 tools/member.py add EMAIL [MONTHS]      # prints the access code and link
  python3 tools/member.py remove EMAIL
  python3 tools/member.py list
  python3 tools/member.py rotate                  # new master key, re-wrap for all active members

Secrets live in private/ (never published): master.key, members.json (email -> code, expiry).
"""
import base64, datetime, hashlib, json, os, secrets, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(ROOT, "private")
OUT = os.path.join(ROOT, "data_branch")          # working copy of the GitHub "data" branch
ITER = 150000
b64 = lambda b: base64.b64encode(b).decode()


def _master(new=False):
    if new:
        raise RuntimeError("Unsafe direct master overwrite disabled; use guarded rekey()")
    p = os.path.join(PRIV, "master.key")
    if not os.path.exists(p):
        os.makedirs(PRIV, exist_ok=True)
        with open(p, "w", encoding="utf8") as f:
            f.write(b64(secrets.token_bytes(32)))
    with open(p, "r", encoding="utf8") as f:
        return base64.b64decode(f.read().strip())


def _members():
    p = os.path.join(PRIV, "members.json")
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf8") as f:
        return json.load(f)


def _save_members(m):
    os.makedirs(PRIV, exist_ok=True)
    with open(os.path.join(PRIV, "members.json"), "w", encoding="utf8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)


def _kid(code):
    return hashlib.sha256(("govradar:" + code).encode()).hexdigest()[:20]


def _wrap(K, code):
    salt = secrets.token_bytes(16)
    kek = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(code.encode())
    iv = secrets.token_bytes(12)
    return {"s": b64(salt), "iv": b64(iv), "w": b64(AESGCM(kek).encrypt(iv, K, None))}


def write_keys():
    K = _master(); today = datetime.date.today().isoformat(); keys = {}
    for email, m in _members().items():
        if m["exp"] >= today:
            keys[_kid(m["code"])] = {**_wrap(K, m["code"]), "exp": m["exp"]}
    os.makedirs(os.path.join(OUT, "m"), exist_ok=True)
    with open(os.path.join(OUT, "m", "keys.json"), "w", encoding="utf8") as f:
        json.dump({"v": 1, "iter": ITER, "updated": today, "keys": keys}, f)
    return len(keys)


def encrypt():
    K = AESGCM(_master()); n = 0
    src = os.path.join(PRIV, "m")
    for L in sorted(os.listdir(src)):
        os.makedirs(os.path.join(OUT, "m", L), exist_ok=True)
        for f in os.listdir(os.path.join(src, L)):
            iv = secrets.token_bytes(12)
            ct = K.encrypt(iv, open(os.path.join(src, L, f), "rb").read(), None)
            json.dump({"iv": b64(iv), "c": b64(ct)}, open(os.path.join(OUT, "m", L, f), "w")); n += 1
    return n


def add(email, months=1):
    m = _members(); email = email.strip().lower()
    code = m.get(email, {}).get("code") or "-".join(secrets.token_hex(2).upper() for _ in range(4))
    start = max(datetime.date.today(), datetime.date.fromisoformat(m[email]["exp"])) if email in m and m[email]["exp"] >= datetime.date.today().isoformat() else datetime.date.today()
    exp = (start + datetime.timedelta(days=31 * int(months))).isoformat()
    m[email] = {"code": code, "exp": exp, "added": datetime.date.today().isoformat()}
    _save_members(m); write_keys()
    return code, exp


def rekey(revoked_email=None):
    # Revoke/rotate without leaving old K in place. Dry data branch: no git push.
    from member_rekey import rekey_local
    return rekey_local(PRIV, OUT, _members(), _wrap, _kid, revoked_email=revoked_email)


def main(a):
    cmd = a[0] if a else "list"
    if cmd == "encrypt": print("encrypted", encrypt(), "files; active keys", write_keys())
    elif cmd == "add":
        code, exp = add(a[1], a[2] if len(a) > 2 else 1)
        print(json.dumps({"email": a[1], "code": code, "exp": exp, "link": f"https://radar.wmm-hoa.com/ko/member/#{code}"}, ensure_ascii=False))
    elif cmd == "remove":
        if len(a) < 2: raise ValueError("remove requires EMAIL")
        print(json.dumps(rekey(a[1]), ensure_ascii=False))
    elif cmd == "rotate":
        print(json.dumps(rekey(), ensure_ascii=False))
    else:
        for k, v in _members().items(): print(k, v["exp"])


if __name__ == "__main__":
    main(sys.argv[1:])
