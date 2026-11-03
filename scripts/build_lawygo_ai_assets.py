#!/usr/bin/env python3
"""Download six user-approved LAWYGO image blobs and optimize to WebP.

Crops remove AI-rendered copy from the LEFT of each concept mockup.
All website text remains real selectable HTML, never image-generated text.
Only official GitHub API blobs from the exact same repository are retrieved.
"""
import base64
import io
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

REPO = "skvive/lawygototal"
MANIFEST = Path("docs/design/LAWYGO_AI_ASSET_BLOBS_20261103.json")
OUT = Path("static/img/design/lawygo-ai-20261103")


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["version"] == "20261103"
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("A GitHub Actions token is required for blob retrieval.")
    OUT.mkdir(parents=True, exist_ok=True)
    for item in data["images"]:
        sha = item["blob_sha"]
        assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)
        headers = {"Accept": "application/vnd.github+json",
                   "Authorization": "Bearer " + token,
                   "X-GitHub-Api-Version": "2022-11-28"}
        url = "https://api.github.com/repos/" + REPO + "/git/blobs/" + sha
        with urlopen(Request(url, headers=headers), timeout=40) as res:
            result = json.load(res)
        if result.get("encoding") != "base64":
            raise ValueError("GitHub blob must be base64")
        content = base64.b64decode(result["content"])
        img = Image.open(io.BytesIO(content)).convert("RGB")
        w, h = img.size
        x0,y0,x1,y1 = item["crop"]
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError("invalid crop")
        img = img.crop((int(w*x0),int(h*y0),int(w*x1),int(h*y1)))
        img = ImageOps.fit(img, (1120,700), method=Image.Resampling.LANCZOS,
                           centering=(0.5,0.48))
        name = item["name"]
        if name not in ("total","journal","wiki","pan","note","pro"):
            raise ValueError("unknown service")
        path = OUT / ("lawygo-" + name + "-ai-20261103.webp")
        img.save(path, "WEBP", quality=71, method=6)
        if not (15_000 <= path.stat().st_size <= 200_000):
            raise ValueError("Unexpected optimized image size " + name)
        print(name, path, img.size, path.stat().st_size)


if __name__ == "__main__":
    main()
