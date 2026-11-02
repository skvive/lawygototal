from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_note_exposes_requested_lawygo_ai_engine_entries():
    note = read("static/note.html")
    requested_tools = {
        "case_search": "판례 자동 추천",
        "doc_summary": "판결문 PDF·이미지 요약",
        "doc_draft": "법률문서 자동작성",
        "law_search": "법률검색",
        "ai_search": "AI 검색",
    }

    assert note.count('data-ai-engine="') == len(requested_tools)
    for slug, label in requested_tools.items():
        assert f'data-ai-engine="{slug}"' in note
        assert f"/board/ai/{slug}" in note
        assert label in note


def test_wiki_reader_is_a_standalone_research_detail_view():
    script = read("static/wiki-page.js")
    stylesheet = read("static/portal-workspaces.css")

    for marker in (
        "wikiReaderCopy",
        "wikiReaderNote",
        "wikiReaderSource",
        "wiki-reader-layout",
        "wiki-reader-summary",
    ):
        assert marker in script or marker in stylesheet

    assert "navigator.clipboard.writeText" in script
    assert "'/p/note'" in script or '"/p/note"' in script


def test_generated_legal_visual_is_used_by_wiki():
    wiki = read("static/wiki.html")
    stylesheet = read("static/portal-workspaces.css")
    asset = ROOT / "static/img/design/legal-knowledge-city.webp"

    assert asset.exists()
    assert "portal-wiki-image" in wiki
    assert "/static/img/design/legal-knowledge-city.webp" in stylesheet


def test_wiki_and_note_keep_shared_platform_navigation():
    for page in ("static/wiki.html", "static/note.html"):
        html = read(page)
        assert "/static/platform-switcher.css" in html
        assert "/static/platform-switcher.js" in html
        assert '<meta name="description"' in html


def test_shared_brand_accessible_name_matches_visible_wordmark():
    shell = read("static/brand-shell.js")

    assert 'aria-label="LAWYGO LEGAL INTELLIGENCE 메인"' in shell

