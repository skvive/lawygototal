from test_engine import c


def test_pan_feed_and_content_endpoints(c):
    r = c.get("/api/feed?kind=all")
    assert r.status_code == 200
    body = r.json()
    assert "contents" in body
    assert isinstance(body["contents"], list)

    r2 = c.get("/api/pan/content?type=blog")
    assert r2.status_code == 200
    assert "items" in r2.json()

    r3 = c.get("/api/pan/lawyers")
    assert r3.status_code == 200
    assert "items" in r3.json()

    assert c.get("/p/pan").status_code == 200
