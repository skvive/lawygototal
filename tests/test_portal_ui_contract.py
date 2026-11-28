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


def test_wiki_text_first_index_and_brand_asset_are_present():
    wiki = read("static/wiki.html")
    stylesheet = read("static/lawygo-wiki-restored-20261111.css")
    assert (ROOT / "static/logo.svg").exists()
    assert 'src="/static/logo.svg"' in wiki
    assert "wref-topic-index" in wiki and "wref-topic-index" in stylesheet
    assert 'id="wikiLatestList"' in wiki
    assert 'id="wikiArticleSource"' in wiki


def test_wiki_and_note_keep_shared_platform_navigation():
    wiki = read("static/wiki.html")
    note = read("static/note.html")
    assert 'aria-label="법률백과 상단 내비게이션"' in wiki
    assert 'href="/p/wiki?view=search"' in wiki
    assert 'href="https://lawygo.com"' in wiki
    assert "/static/platform-switcher.css" in note
    assert "/static/platform-switcher.js" in note
    assert 'href="/p/wiki?view=search"' in note
    for html in (wiki,note):
        assert '<meta name="description"' in html


def test_shared_brand_accessible_name_matches_visible_wordmark():
    shell = read("static/brand-shell.js")

    assert '<a href="/" class="logo">' in shell


def test_home_does_not_repeat_header_module_navigation():
    home = read("static/index.html")
    assert "v7-fastbar" not in home
    assert "v7-products" not in home
    assert "v7-solution-cards" not in home
    assert 'class="v7-three-col v7-two-col"' in home
    assert "v7-news-column" in home and "v7-wiki-column" in home
    assert "/static/lawygo-editorial-portal-v8.js" in home


def test_note_compact_welcome_keeps_interactive_engine():
    note = read("static/note.html")
    css = read("static/lawygo-editorial-portal-v8.css")
    assert 'class="lawygo-ai-icon"' not in note
    assert 'class="lawygo-ai-brand-mark"' not in note
    assert 'class="lawygo-ai-kicker"' in note
    for part in ("lnw-chat-new", "lnw-chat-messages", "lnw-chat-form",
                 "lnw-chat-input", "lnw-chat-sources", "data-lnw-mode="):
        assert part in note
    assert "v10 compact editorial layout" in css
    assert ".lawygo-ai-welcome{margin:0 auto" in css


def test_pan_note_korean_first_text_layout():
    pan = read("static/pan.html")
    note = read("static/note.html")
    css = read("static/lawygo-editorial-portal-v8.css")
    script = read("static/pan-published-v2-20261108.js")
    assert "법률 영상·전문가 콘텐츠" in pan
    assert "법률 콘텐츠 홈" in pan
    assert "미국 로펌 분석" in script
    assert "영문 원문 한국어 자동번역" in script
    assert "법률자료 검색과 문서 정리" in note
    assert "문서 서식 선택" in note
    assert 'id="lnw-chat-form"' in note and 'id="noteDraftContent"' in note
    assert note.index('id="note-chat-workspace"') < note.index('id="note-editor"')
    assert "wiki-native-workspace" not in note
    assert 'href="/p/wiki?view=search"' in note
    assert "Korean-first PAN / text-first NOTE" in css
