"""Source ingestion must not invent posts or collapse distinct Blogger URLs."""
import unittest
import pan_public_feed as pan

class RealSourceTests(unittest.TestCase):
    def test_unique_blogger_post_ids(self):
        data={"feed":{"generator":{"$t":"Blogger"},"link":[{"rel":"alternate","href":"https://2yourlawyer.blogspot.com"}],"entry":[]}}
        for i in range(2):
            url=f"https://2yourlawyer.blogspot.com/2026/11/article-{i}.html"
            data["feed"]["entry"].append({"id":{"$t":"tag:blogger.com,1999:blog-7550124187276091004.post-"+str(i)},
                "title":{"$t":"법률 판례 "+str(i)}, "content":{"$t":"변호사 판례 해설"},
                "link":[{"rel":"alternate","href":url}],"published":{"$t":"2026-11-08T00:00:00+09:00"}})
        posts=pan._parse_blogger_json(data,"LAWYGO TEST")
        self.assertEqual(len(posts),2)
        self.assertNotEqual(posts[0]["id"],posts[1]["id"])
        self.assertTrue(all(x["url"].startswith("https://") for x in posts))

    def test_real_videos_are_kept_with_accurate_source_context(self):
        items=pan._verified_source_starters()
        videos=[x for x in items if x["content_type"] in ("video","shorts")]
        self.assertGreaterEqual(len(videos),8)
        self.assertTrue(all(pan._is_legal_topic(x) for x in videos))
        self.assertEqual(len({x["id"] for x in items}),len(items))
        self.assertTrue(all(x["live"] is False for x in items))

    def test_newswire_rss_is_source_limited(self):
        xml="""<rss><channel>
        <item><title>법률 분야 소송 보도자료</title>
        <link>https://www.newswire.co.kr/newsRead.php?no=1234</link>
        <description>법률사무소 소송 사례</description><pubDate>Sun, 08 Nov 2026 00:00:00 +0900</pubDate></item>
        <item><title>법률 위조 출처</title>
        <link>https://evil.example.net/untrusted</link></item>
        </channel></rss>"""
        results=pan._parse_newswire_rss(xml)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]["content_type"],"newswire")
        self.assertIn("뉴스와이어",results[0]["source"])
        self.assertEqual(results[0]["source_kind"],"press-release")

if __name__ == "__main__":
    unittest.main()
