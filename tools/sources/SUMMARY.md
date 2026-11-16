# Source registry summary (generated — do not edit by hand)

- Candidates: **232** (international 16, national-api 9, national-portal 193, sub-national 14)
- Collect status: **PASS 7 / FAIL 5 / UNKNOWN 220**
- PASS = a collector has actually returned notices from this source. Candidates are not live connections.

| Status | ID | Source | Note |
|---|---|---|---|
| PASS | INT-EU-TED | EU TED Search API v3 | Connected (feed_more.ted) |
| PASS | INT-WB-AWARDS | World Bank contract award notices | Connected (feed_intel.awards) |
| PASS | INT-WB-NOTICES | World Bank procurement notices API | Connected (feed_tenders.worldbank) |
| PASS | INT-WB-PIPELINE | World Bank projects API (pipeline) | Connected (feed_intel.pipeline) |
| PASS | NAT-GB-CF | Contracts Finder OCDS search | Connected in review branch (feed_more.ukcf); notice URL = uuid part of release id, checked against live notice pages |
| PASS | NAT-GB-FTS | Find a Tender Service OCDS API | Connected (feed_more.uk) |
| PASS | NAT-UA-PROZORRO | Prozorro public API | Connected in review branch (feed_more.prozorro); up to 400 new detail checks per run with a cache, unchecked count reported in sources_status.json; titles in Ukrainian |
| FAIL | INT-ADB | Project tenders | robots.txt disallows /projects/tenders/rss and csv exports; listing is JS-rendered |
| FAIL | INT-AFDB | Procurement | HTTP 403 to automated requests |
| FAIL | INT-UNDP | Procurement notices | robots.txt: Disallow / for all agents |
| FAIL | INT-UNGM | UN Global Marketplace public notices | HTTP 403 to automated requests; redistribution terms to be verified |
| FAIL | NAT-CA-CANADABUYS | CanadaBuys open tender notices CSV | Collector written and tested (43 notices on 2026-11-16) but disabled: robots.txt allows only Googlebot/bingbot. Data is under the Open Government Licence — owner decision needed |
