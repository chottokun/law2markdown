"""Tests for reference analyzer and citation graph builder."""

from law2markdown.analyzer.reference import (
    build_reference_graph,
    extract_references_from_text,
    kanji_to_int,
)
from law2markdown.models import ArticleContent, LawMetadata
from law2markdown.renderer.frontmatter import render_article_frontmatter
from law2markdown.renderer.markdown import render_article_markdown


def test_kanji_to_int():
    assert kanji_to_int("一") == 1
    assert kanji_to_int("十二") == 12
    assert kanji_to_int("百二十三") == 123
    assert kanji_to_int("四百三十六") == 436
    assert kanji_to_int("二千十五") == 2015


def test_extract_references():
    text = (
        "労働条件については、前条の規定によるほか、第十二条及び第百二十三条第一項の規定を準用する。"
        "詳細は政令で定める。"
    )
    refs = extract_references_from_text(text)
    assert "前条" in refs["relative"]
    assert "第十二条" in refs["articles"]
    assert "第百二十三条" in refs["articles"]
    assert any("政令で定める" in d for d in refs["delegations"])


def test_build_reference_graph():
    # Art 1 refers to Art 2 and has "次条"
    # Art 2 refers to "前条" (which resolves to Art 1)
    # Art 3 refers to Art 1
    art1 = ArticleContent(
        article_id="art_001_第一条",
        num="1",
        title="第一条",
        caption="（目的）",
    )
    art2 = ArticleContent(
        article_id="art_002_第二条",
        num="2",
        title="第二条",
        caption="（定義）",
    )
    art3 = ArticleContent(
        article_id="art_003_第三条",
        num="3",
        title="第三条",
        caption="（適用）",
    )
    # Give articles paragraph text
    from law2markdown.models import ParagraphContent

    art1.paragraphs = [
        ParagraphContent(sentences=["第一条本文。第二条の基準に従う。詳細は次条による。"])
    ]
    art2.paragraphs = [ParagraphContent(sentences=["前条の規定に基づく。"])]
    art3.paragraphs = [ParagraphContent(sentences=["第一条を準用する。"])]

    articles = [art1, art2, art3]
    build_reference_graph(articles)

    # Check art1
    assert "art_002_第二条" in art1.outbound_references
    assert "art_002_第二条" in art1.inbound_references
    assert "art_003_第三条" in art1.inbound_references

    # Check art2
    assert "art_001_第一条" in art2.outbound_references
    assert "art_001_第一条" in art2.inbound_references

    # Check Frontmatter output
    meta = LawMetadata(title="テスト法")
    fm = render_article_frontmatter(meta, art1)
    assert "outbound_references:" in fm
    assert '  - "art_002_第二条"' in fm
    assert "inbound_references:" in fm
    assert '  - "art_003_第三条"' in fm

    # Check Markdown body output (appended reference section, ASIS body preserved)
    md = render_article_markdown(meta, art1, articles_map={a.article_id: a for a in articles})
    assert "## 参照・関連規定" in md
    assert "[第二条（定義）](./art_002_第二条.md)" in md
