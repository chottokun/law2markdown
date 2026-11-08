"""Tests for child anchors and multi-level syntax offsets."""

from law2markdown.models import ArticleContent, ItemContent, LawMetadata, ParagraphContent
from law2markdown.renderer.frontmatter import render_article_frontmatter
from law2markdown.renderer.markdown import render_article_markdown


def test_child_anchors_generation_and_offsets():
    meta = LawMetadata(title="アンカーテスト法")
    art = ArticleContent(
        article_id="art_001_第一条",
        num="1",
        title="第一条",
        caption="（多段階条文）",
        paragraphs=[
            ParagraphContent(
                num="",
                sentences=["第一項の本文です。労働条件の基準を定める。"],
                items=[
                    ItemContent(
                        title="一",
                        sentences=["賃金に関する事項。"],
                        subitems=[
                            ItemContent(title="イ", sentences=["基本給に関する事項。"]),
                        ],
                    ),
                    ItemContent(title="二", sentences=["労働時間に関する事項。"]),
                ],
            ),
            ParagraphContent(
                num="２",
                sentences=["第二項の本文です。前項の規定を適用する。"],
            ),
        ],
    )

    body = render_article_markdown(meta, art)

    # 1. Verify HTML anchor tags in body
    assert '<a id="p1"></a>' in body
    assert '<a id="p1-i1"></a>' in body
    assert '<a id="p1-i1-s1"></a>' in body
    assert '<a id="p1-i2"></a>' in body
    assert '<a id="p2"></a>' in body

    # 2. Verify child_anchors populated on art
    assert len(art.child_anchors) >= 5
    anchor_ids = [a.id for a in art.child_anchors]
    assert "p1" in anchor_ids
    assert "p1-i1" in anchor_ids
    assert "p1-i1-s1" in anchor_ids
    assert "p1-i2" in anchor_ids
    assert "p2" in anchor_ids

    # 3. Check offsets correspond to actual text slice in body
    for anchor in art.child_anchors:
        sliced = body[anchor.start_offset : anchor.end_offset]
        assert f'<a id="{anchor.id}"></a>' in sliced

    # 4. Check Frontmatter output
    fm = render_article_frontmatter(meta, art)
    assert "child_anchors:" in fm
    assert '- id: "p1"' in fm
    assert '  level: "paragraph"' in fm
    assert "  start_offset:" in fm
    assert "  end_offset:" in fm
