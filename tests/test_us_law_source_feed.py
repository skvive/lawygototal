import unittest
from us_legal_sources import verified_us_articles,parse_us_rss
class TestUSLegal(unittest.TestCase):
 def test_verified_translation(self):
  rows=verified_us_articles()
  self.assertGreaterEqual(len(rows),8)
  self.assertTrue(all(x["title_ko"] and x["summary_ko"] and x["source_region"]=="US" for x in rows))
  self.assertEqual(len({x["id"] for x in rows}),len(rows))
 def test_feed_domain_limit(self):
  xml="<rss><channel><item><title>Data Privacy Law</title><link>https://www.huntonprivacyblog.com/privacy</link><pubDate>Sun, 08 Nov 2026 00:00:00 GMT</pubDate></item><item><title>Privacy Law</title><link>https://evil.com/privacy</link></item></channel></rss>"
  posts=parse_us_rss(xml,"Hunton Andrews Kurth","huntonprivacyblog.com")
  self.assertEqual(len(posts),1)
  self.assertEqual(posts[0]["translation_status"],"source-en")
if __name__=="__main__":unittest.main()
