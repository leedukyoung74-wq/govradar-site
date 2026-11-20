import base64
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import member
import member_rekey

class MemberRekeyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.priv = self.root / "private"
        self.out = self.root / "data_branch"
        (self.out / "m").mkdir(parents=True)
        for lang in member_rekey.LANGS:
            p = self.priv / "m" / lang
            p.mkdir(parents=True)
            (p / "brief.json").write_text('{"analysis":"premium demo"}',encoding="utf8")
        self.vault = (self.out / "m" / "vault.json")
        self.vault.write_bytes(b'{"protected-existing-data":true}')
        self.old_priv, self.old_out = member.PRIV, member.OUT
        member.PRIV, member.OUT = str(self.priv), str(self.out)
        member._master()
        self.members = {
            "alice@example.org": {"code":"ALICE-TEST-RANDOM", "exp":"2099-01-01", "added":"2026-11-20"},
            "bob@example.org": {"code":"BOB-TEST-RANDOM", "exp":"2099-01-01", "added":"2026-11-20"}
        }
        member._save_members(self.members)
        member.encrypt()
        member.write_keys()
        self.old_k = member._master()
        self.original_registry = (self.priv / "members.json").read_bytes()
        self.original_data = (self.out / "m" / "ko" / "brief.json").read_bytes()

    def tearDown(self):
        member.PRIV, member.OUT = self.old_priv, self.old_out
        self.tmp.cleanup()

    def test_removal_rotates_master_and_preserves_nonmember_vault(self):
        result=member.rekey("alice@example.org")
        self.assertEqual(result["status"],"LOCAL_REKEY_PREPARED_NOT_PUBLISHED")
        self.assertEqual(result["remaining_members"],1)
        self.assertEqual(result["active_wrapped_keys"],1)
        self.assertEqual(result["encrypted_files"],7)
        self.assertTrue(result["requires_data_branch_publish_and_verification"])
        self.assertFalse(result["production_deployed"])
        self.assertFalse(result["previously_downloaded_material_recalled"])
        new_key=member._master()
        self.assertNotEqual(self.old_k,new_key)
        self.assertEqual(self.vault.read_bytes(), b'{"protected-existing-data":true}')
        data=json.loads((self.out/"m"/"ko"/"brief.json").read_text("utf8"))
        iv,ct=base64.b64decode(data["iv"]),base64.b64decode(data["c"])
        self.assertEqual(AESGCM(new_key).decrypt(iv,ct,None),b'{"analysis":"premium demo"}')
        with self.assertRaises(InvalidTag): AESGCM(self.old_k).decrypt(iv,ct,None)
        registry=member._members()
        self.assertEqual(set(registry),{"bob@example.org"})
        keys=json.loads((self.out/"m"/"keys.json").read_text())
        self.assertEqual(set(keys["keys"]),{member._kid(self.members["bob@example.org"]["code"])})
        wrapped=keys["keys"][member._kid(self.members["bob@example.org"]["code"])]
        kek=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,
            salt=base64.b64decode(wrapped["s"]),iterations=keys["iter"]).derive(
                self.members["bob@example.org"]["code"].encode())
        self.assertEqual(AESGCM(kek).decrypt(base64.b64decode(wrapped["iv"]),
                          base64.b64decode(wrapped["w"]),None),new_key)
        self.assertFalse((self.priv/".wmm-member-rekey.lock").exists())
        self.assertEqual([p.name for p in self.out.iterdir() if p.name.startswith(".wmm")],[])

    def test_unknown_member_does_not_change_encryption_or_registry(self):
        with self.assertRaisesRegex(ValueError,"Unknown member"):
            member.rekey("missing@example.org")
        self.assertEqual(member._master(),self.old_k)
        self.assertEqual((self.priv/"members.json").read_bytes(),self.original_registry)
        self.assertEqual((self.out/"m"/"ko"/"brief.json").read_bytes(),self.original_data)

    def test_missing_private_language_source_aborts_before_rotation(self):
        (self.priv/"m"/"ar"/"brief.json").unlink()
        (self.priv/"m"/"ar").rmdir()
        with self.assertRaisesRegex(ValueError,"Missing private member locale"):
            member.rekey("alice@example.org")
        self.assertEqual(member._master(),self.old_k)

    def test_simulated_failure_restores_master_registry_and_ciphertext(self):
        original_replace = os.replace
        count = 0
        def fail_once(src,dst):
            nonlocal count
            count += 1
            if count==3:
                raise OSError("simulated disk interruption")
            return original_replace(src,dst)
        with patch.object(member_rekey.os,"replace",side_effect=fail_once):
            with self.assertRaisesRegex(OSError,"simulated disk"):
                member.rekey("alice@example.org")
        self.assertEqual(member._master(),self.old_k)
        self.assertEqual((self.priv/"members.json").read_bytes(),self.original_registry)
        self.assertEqual((self.out/"m"/"ko"/"brief.json").read_bytes(),self.original_data)
        self.assertFalse((self.priv/".wmm-member-rekey.lock").exists())
        self.assertEqual(self.vault.read_bytes(),b'{"protected-existing-data":true}')

    def test_rotation_without_removal_changes_key_for_all_active_members(self):
        result=member.rekey()
        self.assertEqual(result["remaining_members"],2)
        self.assertNotEqual(member._master(),self.old_k)
        keys=json.loads((self.out/"m"/"keys.json").read_text())
        self.assertEqual(len(keys["keys"]),2)

if __name__=="__main__":
    unittest.main()
