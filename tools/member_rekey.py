"""Fail-closed local member rekey and revocation.

Rekeys all premium ciphertext (from private/m) and rebuilds public key wraps.
Stages and validates complete candidate files before swapping either the local
master key or the data branch m/ directory. No remote push or emails are sent.

Shared-master limitation: a revoked member may retain a copy of previously
downloaded plaintext/ciphertext and its old key. Rekey restricts FUTURE files,
it cannot erase prior downloads. Do not call this "live revoked" before the
data branch update is published and verified.
"""
from __future__ import annotations

import base64
from datetime import date
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LANGS = ("ko", "en", "es", "fr", "ar", "vi", "id")
def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")

def _reject_symlinks(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("Symlinked member source/output directory is not allowed: " + str(path))
    for current in path.rglob("*"):
        if current.is_symlink():
            raise ValueError("Symlink in member data is not allowed: " + str(current))

def _write_private(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf8")
    try: path.chmod(0o600)
    except OSError: pass

def rekey_local(priv_root: str, output_root: str, members: dict,
                wrap, key_id, *, revoked_email: str | None = None) -> dict:
    priv = Path(priv_root)
    output = Path(output_root)
    source = priv / "m"
    target = output / "m"
    master_file = priv / "master.key"
    members_file = priv / "members.json"
    if (not priv.is_dir() or not output.is_dir() or not source.is_dir()
            or not target.is_dir() or not master_file.is_file()
            or not members_file.is_file()):
        raise ValueError("Private member sources, master, registry and data branch output must already exist")
    _reject_symlinks(source)
    _reject_symlinks(target)

    # Never overwrite unknown or incomplete locale sources: rotation could
    # otherwise truncate member content while seeming successful.
    for lang in LANGS:
        folder = source / lang
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Missing private member locale source: " + lang)

    if not isinstance(members, dict):
        raise ValueError("Invalid member registry")
    remaining = dict(members)
    if revoked_email is not None:
        email = revoked_email.strip().lower()
        if not email or email not in remaining:
            raise ValueError("Unknown member; no changes made")
        remaining.pop(email)

    for email, member in remaining.items():
        if (not isinstance(member, dict)
                or not isinstance(member.get("code"), str)
                or not isinstance(member.get("exp"), str)):
            raise ValueError("Incomplete member registry record for: " + email)
        date.fromisoformat(member["exp"])
    sources = []
    for lang in LANGS:
        directory = source / lang
        for path in directory.iterdir():
            if not path.is_file() or path.is_symlink():
                raise ValueError("Unexpected member source entry: " + str(path))
            sources.append((lang, path))
    if not sources:
        raise ValueError("No source files to re-encrypt; refusing to rotate")

    lock = priv / ".wmm-member-rekey.lock"
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("Another member rekey is in progress or requires recovery")
    os.close(fd)

    stage_priv = None
    stage_out = None
    backup_master = priv / (".wmm-master-backup-" + secrets.token_hex(8))
    backup_members = priv / (".wmm-members-backup-" + secrets.token_hex(8))
    backup_data = output / (".wmm-data-backup-" + secrets.token_hex(8))
    completed = False
    try:
        stage_priv = Path(tempfile.mkdtemp(prefix=".wmm-rekey-priv-", dir=priv))
        stage_out = Path(tempfile.mkdtemp(prefix=".wmm-rekey-data-", dir=output))
        staged_m = stage_out / "m"
        shutil.copytree(target, staged_m)
        for lang in LANGS:
            staged_lang = staged_m / lang
            if staged_lang.exists():
                shutil.rmtree(staged_lang)
            staged_lang.mkdir(parents=True)
        # Keep data/m/vault.json and other non-member metadata unchanged.
        master = secrets.token_bytes(32)
        cipher = AESGCM(master)
        n = 0
        for lang, src_file in sources:
            raw = src_file.read_bytes()
            nonce = secrets.token_bytes(12)
            payload = {"iv": _b64(nonce), "c": _b64(cipher.encrypt(nonce, raw, None))}
            destination = staged_m / lang / src_file.name
            destination.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf8")
            # Verify new ciphertext is readable using the rotated master before any swap.
            sample = json.loads(destination.read_text("utf8"))
            decrypted = cipher.decrypt(base64.b64decode(sample["iv"]),
                                       base64.b64decode(sample["c"]), None)
            if decrypted != raw:
                raise ValueError("Ciphertext verification failed")
            n += 1
        today = date.today().isoformat()
        keys = {}
        for email, record in remaining.items():
            if record["exp"] >= today:
                kid = key_id(record["code"])
                if kid in keys:
                    raise ValueError("Duplicate member key identifier")
                keys[kid] = {**wrap(master, record["code"]), "exp": record["exp"]}
        staged_keys = {"v": 1, "iter": 150000, "updated": today, "keys": keys}
        (staged_m / "keys.json").write_text(json.dumps(staged_keys), encoding="utf8")
        _write_private(stage_priv / "master.key", _b64(master))
        _write_private(stage_priv / "members.json",
                       json.dumps(remaining, ensure_ascii=False, indent=1))

        # All writes below are local. No git push, Cloudflare update or external request.
        os.replace(target, backup_data)
        os.replace(staged_m, target)
        os.replace(master_file, backup_master)
        os.replace(stage_priv / "master.key", master_file)
        os.replace(members_file, backup_members)
        os.replace(stage_priv / "members.json", members_file)
        completed = True
        return {
            "status": "LOCAL_REKEY_PREPARED_NOT_PUBLISHED",
            "revoked_member": bool(revoked_email is not None),
            "remaining_members": len(remaining),
            "active_wrapped_keys": len(keys),
            "encrypted_files": n,
            "production_deployed": False,
            "requires_data_branch_publish_and_verification": True,
            "previously_downloaded_material_recalled": False,
        }
    finally:
        if not completed:
            # Restore every original; a missing backup means the original was
            # never moved. If recovery fails, leave the lock in place for
            # explicit operator inspection instead of allowing another rekey.
            try:
                if backup_members.exists():
                    members_file.unlink(missing_ok=True)
                    os.replace(backup_members, members_file)
                if backup_master.exists():
                    master_file.unlink(missing_ok=True)
                    os.replace(backup_master, master_file)
                if backup_data.exists():
                    if target.exists():
                        shutil.rmtree(target)
                    os.replace(backup_data, target)
            except BaseException:
                raise RuntimeError("Member rekey recovery failed; inspect private lock and backups")
        else:
            backup_members.unlink(missing_ok=True)
            backup_master.unlink(missing_ok=True)
            if backup_data.exists():
                shutil.rmtree(backup_data)
        if stage_priv is not None:
            shutil.rmtree(stage_priv, ignore_errors=True)
        if stage_out is not None:
            shutil.rmtree(stage_out, ignore_errors=True)
        lock.unlink(missing_ok=True)
