"""Tests for legal definition analyzer and definitions.md generator."""

from law2markdown.analyzer.definition import (
    build_definition_registry,
    extract_definitions_from_text,
)
from law2markdown.models import ArticleContent, LawMetadata, ParagraphContent
from law2markdown.renderer.frontmatter import render_definitions_frontmatter
from law2markdown.renderer.markdown import render_article_markdown, render_definitions_markdown


def test_extract_definitions_from_text():
    text1 = (
        "この法律において「労働者」とは、職業の種類を問わず、"
        "事業又は事務所に使用される者で、賃金を支払われる者をいう。"
    )
    defs1 = extract_definitions_from_text(text1)
    assert len(defs1) == 1
    assert defs1[0].term == "労働者"
    assert "事業又は事務所に使用される者で" in defs1[0].definition_text

    text2 = "労働条件通知書（以下「通知書」という。）を交付しなければならない。"
    defs2 = extract_definitions_from_text(text2)
    assert len(defs2) == 1
    assert defs2[0].term == "通知書"


def test_build_definition_registry():
    art1 = ArticleContent(
        article_id="art_001_第一条",
        num="1",
        title="第一条",
        paragraphs=[
            ParagraphContent(
                sentences=[
                    "この法律において「賃金」とは、労働の対償として使用者が労働者に支払うすべてのものをいう。"
                ]
            )
        ],
    )
    art2 = ArticleContent(
        article_id="art_002_第二条",
        num="2",
        title="第二条",
        paragraphs=[
            ParagraphContent(
                sentences=["使用者は、労働者に対して適正な賃金を支払わなければならない。"]
            )
        ],
    )

    articles = [art1, art2]
    registry = build_definition_registry(articles)

    assert len(registry) == 1
    assert registry[0].term == "賃金"
    assert registry[0].article_id == "art_001_第一条"

    assert "賃金" in art1.defined_terms
    assert "賃金" in art2.referenced_terms

    # Test rendering definitions.md
    meta = LawMetadata(title="テスト法", law_id="322AC0000000049")
    fm = render_definitions_frontmatter(meta, timestamp="2026-11-08T00:00:00Z")
    assert "type: law_definitions" in fm
    assert 'title: "テスト法 用語定義レジストリ"' in fm

    md = render_definitions_markdown(meta, registry)
    assert "# テスト法 用語定義レジストリ" in md
    assert '<a id="賃金"></a>' in md
    assert "[第一条](./articles/art_001_第一条.md)" in md

    # Test article markdown has definitions section
    art2_md = render_article_markdown(meta, art2, definitions=registry)
    assert "## 定義用語" in art2_md
    assert "[賃金](../definitions.md#賃金)" in art2_md
