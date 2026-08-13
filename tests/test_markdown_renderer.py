"""Tests for markdown and frontmatter renderers."""

from law2markdown.models import (
    ArticleContent,
    ItemContent,
    LawMetadata,
    ParagraphContent,
)
from law2markdown.renderer.frontmatter import render_article_frontmatter
from law2markdown.renderer.markdown import render_article_markdown


def test_render_frontmatter():
    meta = LawMetadata(
        era="Showa",
        year=22,
        num=49,
        law_type="Act",
        law_num_text="昭和二十二年法律第四十九号",
        title="労働基準法",
        law_id="322AC0000000049",
    )
    art = ArticleContent(
        article_id="art_001",
        num="1",
        title="第一条",
        caption="（労働条件の原則）",
        chapter="第一章　総則",
    )
    fm = render_article_frontmatter(meta, art, timestamp="2026-08-13T00:00:00Z")
    assert "type: law_article" in fm
    assert 'title: "労働基準法 第一条"' in fm
    assert 'law_num: "昭和二十二年法律第四十九号"' in fm
    assert 'chapter: "第一章　総則"' in fm


def test_render_article_markdown():
    meta = LawMetadata(title="労働基準法")
    art = ArticleContent(
        article_id="art_001",
        num="1",
        title="第一条",
        caption="（労働条件の原則）",
        chapter="第一章　総則",
        paragraphs=[
            ParagraphContent(
                num="",
                sentences=[
                    "労働条件は、労働者が人たるに値する生活を営むための必要を満たすものでなければならない。"
                ],
            ),
            ParagraphContent(
                num="２",
                sentences=["この法律で定める労働条件の基準は最低のものである。"],
                items=[
                    ItemContent(title="一", sentences=["第一号要件"]),
                ],
            ),
        ],
    )
    md = render_article_markdown(meta, art)
    assert "### （労働条件の原則）" in md
    assert "# 第一条" in md
    assert "**階層文脈**: [労働基準法](../index.md) > 第一章　総則" in md
    expected_body = (
        "労働条件は、労働者が人たるに値する生活を営むための必要を満たすものでなければならない。"
    )
    assert expected_body in md
    assert "**（２）** この法律で定める労働条件の基準は最低のものである。" in md
    assert "  * **一** 第一号要件" in md
