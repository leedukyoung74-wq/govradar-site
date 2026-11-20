"""Static QA for cross-site intake contract. No endpoint, user data or paid API."""
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCHEMA=ROOT/"schemas"/"wmm_cross_site_intake_v1.schema.json"

class IntakeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema=json.loads(SCHEMA.read_text(encoding="utf8"))

    def test_all_six_business_surfaces_have_route_keys(self):
        actual=set(self.schema["properties"]["site"]["enum"])
        self.assertEqual(actual,{"wmm","govradar","gcsme-korea","playground",
                                 "world-miracle-makers","preparedness"})

    def test_consent_is_explicit_and_marketing_is_optional(self):
        s=self.schema
        self.assertEqual(s["properties"]["privacy_consent"]["const"],True)
        self.assertIn("privacy_consent",s["required"])
        self.assertIn("marketing_consent",s["required"])
        self.assertEqual(s["properties"]["marketing_consent"]["type"],"boolean")

    def test_payload_is_bounded_and_unknown_fields_rejected(self):
        s=self.schema
        self.assertFalse(s["additionalProperties"])
        self.assertLessEqual(s["properties"]["message"]["maxLength"],5000)
        self.assertLessEqual(s["properties"]["reply_email"]["maxLength"],254)

if __name__=="__main__":
    unittest.main()
