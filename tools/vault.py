"""Encrypted carry-over of non-public working files between sessions (scheduled runs start fresh).
pack:   export/ + private/members.json + private/tasks.json + private/foresight_country.json -> data_branch/m/vault.json (AES-GCM, master key)
unpack: data_branch/m/vault.json -> files (needs private/master.key)"""
import base64, hashlib, io, json, os, secrets, sys, tarfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.path.join(ROOT, "private", "master.key"); OUT = os.path.join(ROOT, "data_branch", "m", "vault.json")
ITEMS = ["export", "private/members.json", "private/tasks.json", "private/foresight_country.json", "src/i18n_data"]   # i18n_data: daily translations (2026-11-17)
k = lambda: AESGCM(base64.b64decode(open(KEY).read().strip()))
MARK = os.path.join(ROOT, "private", ".vault_sha")   # which vault this working folder matches (publish_cf.sh checks it)
def mark(): open(MARK, "w").write(hashlib.sha256(open(OUT, "rb").read()).hexdigest())
def pack():
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w:gz") as t:
        for it in ITEMS:
            p = os.path.join(ROOT, it)
            if os.path.exists(p): t.add(p, arcname=it)
    iv = secrets.token_bytes(12)
    json.dump({"iv": base64.b64encode(iv).decode(), "c": base64.b64encode(k().encrypt(iv, bio.getvalue(), None)).decode()}, open(OUT, "w"))
    mark(); print("packed", os.path.getsize(OUT), "bytes")
def unpack():
    j = json.load(open(OUT)); raw = k().decrypt(base64.b64decode(j["iv"]), base64.b64decode(j["c"]), None)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as t: t.extractall(ROOT, filter="data")
    mark(); print("unpacked")
if __name__ == "__main__": {"pack": pack, "unpack": unpack}[sys.argv[1]]()
