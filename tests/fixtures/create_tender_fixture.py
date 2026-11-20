"""Generate synthetic tenders inside CI for generated HTML QA, never real notices."""
import datetime
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
EXPORT=ROOT/"export"/"countries"
if EXPORT.exists() and any(EXPORT.glob("*.json")):
    raise SystemExit("Refusing to mix synthetic QA records with existing export data")
EXPORT.mkdir(parents=True,exist_ok=True)
today=datetime.datetime.now(datetime.timezone.utc).date()
future=(today+datetime.timedelta(days=90)).isoformat()
past=(today-datetime.timedelta(days=90)).isoformat()
fixture={
  "id":"KR",
  "data":{
    "agenda":["WMM QA synthetic country summary — NOT A REAL GOVERNMENT NOTICE"],
    "tenders":[
      {"title":"WMM_QA_SYNTHETIC_FUTURE_TENDER","buyer":"WMM QA ONLY", "deadline":future,
       "url":"https://example.org/wmm-qa-future", "added":today.isoformat()},
      {"title":"WMM_QA_SYNTHETIC_PAST_TENDER","buyer":"WMM QA ONLY", "deadline":past,
       "url":"https://example.org/wmm-qa-past", "added":past},
    ],
    "en":{"tenders":[
      {"title":"WMM_QA_SYNTHETIC_FUTURE_TENDER","buyer":"WMM QA ONLY"},
      {"title":"WMM_QA_SYNTHETIC_PAST_TENDER","buyer":"WMM QA ONLY"},
    ]},
    "updated":today.isoformat(),
  }
}
(EXPORT/"KR.json").write_text(json.dumps(fixture,ensure_ascii=False),encoding="utf8")
(ROOT/"wmm_qa_fixture_dates.json").write_text(json.dumps({"future":future,"past":past}),encoding="utf8")
print("synthetic fixture created for test-only offline build:",future,past)
