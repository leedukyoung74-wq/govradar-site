from datetime import datetime
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from pipeline.audit_feeds import KST
from prophecy_watch import todays_links
from public_notices import parse_feed, publication


class PublicNoticesTest(unittest.TestCase):
    def test_date_only_is_not_a_time(self):
        self.assertEqual(publication(" 2026-11-20 "), {"date": "2026-11-20", "precision": "day"})
        self.assertEqual(publication("Fri, 20 Nov 2026 23:35:00 GMT")["kst"], "2026-11-21T08:35:00+09:00")
        self.assertEqual(publication("Wed, 18 Nov 2026 18:30:42 CET")["kst"], "2026-11-19T02:30:42+09:00")

    def test_feed_titles_are_only_metadata_and_duplicate_links_are_removed(self):
        item = b"<item><title>notice</title><link>https://example.org/notice#one</link><pubDate>2026-11-20</pubDate></item>"
        result = parse_feed(b"<rss><channel>" + item + item + b"</channel></rss>", {"example.org"})
        self.assertEqual(result[0]["url"], "https://example.org/notice")
        self.assertEqual(len(result), 1)
        with self.assertRaises(ValueError):
            parse_feed(b"<rss><channel>" + item + b"</channel></rss>", {"not-allowed.example"})

    def test_xml_entity_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_feed(b'<!DOCTYPE rss [<!ENTITY x "hello">]><rss><channel/></rss>', {"example.org"})

    def test_prophecy_history_is_deduplicated_and_uses_kst_date(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "history.jsonl"
            row = '{"video_id":"ABCDEFGHIJK","published_at":"2026-11-20T23:00:00+00:00","person":"Example","title":"Lecture","status":"official_channel_publication"}'
            source.write_text(row + "\n" + row + "\n", encoding="utf-8")
            items = todays_links(source, datetime(2026, 11, 21, 12, tzinfo=KST))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["state"], "source_publication_only")
