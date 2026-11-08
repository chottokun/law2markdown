"""Tests for hierarchy parsing and hierarchy_path generation."""

import pytest

from law2markdown.models import ArticleContent, LawMetadata
from law2markdown.parser.xml_parser import parse_law_xml
from law2markdown.renderer.frontmatter import render_article_frontmatter
from law2markdown.renderer.markdown import render_article_markdown


@pytest.fixture
def multi_hierarchy_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="5" Num="100" LawType="Act" Lang="ja">
  <LawNum>令和五年法律第百号</LawNum>
  <LawBody>
    <LawTitle>階層テスト法</LawTitle>
    <MainProvision>
      <Part Num="1">
        <PartTitle>第一編　総則</PartTitle>
        <Chapter Num="1">
          <ChapterTitle>第一章　目的及び定義</ChapterTitle>
          <Section Num="1">
            <SectionTitle>第一節　目的</SectionTitle>
            <Article Num="1">
              <ArticleCaption>（目的）</ArticleCaption>
              <ArticleTitle>第一条</ArticleTitle>
              <Paragraph Num="1">
                <ParagraphNum/>
                <ParagraphSentence>
                  <Sentence>この法律は、テストを目的とする。</Sentence>
                </ParagraphSentence>
              </Paragraph>
            </Article>
          </Section>
          <Section Num="2">
            <SectionTitle>第二節　定義</SectionTitle>
            <Article Num="2">
              <ArticleCaption>（定義）</ArticleCaption>
              <ArticleTitle>第二条</ArticleTitle>
              <Paragraph Num="1">
                <ParagraphNum/>
                <ParagraphSentence>
                  <Sentence>この法律において「テスト」とは、試験をいう。</Sentence>
                </ParagraphSentence>
              </Paragraph>
            </Article>
          </Section>
        </Chapter>
        <Chapter Num="2">
          <ChapterTitle>第二章　手続</ChapterTitle>
          <Article Num="3">
            <ArticleTitle>第三条</ArticleTitle>
            <Paragraph Num="1">
              <ParagraphNum/>
              <ParagraphSentence>
                <Sentence>手続を行うものとする。</Sentence>
              </ParagraphSentence>
            </Paragraph>
          </Article>
        </Chapter>
      </Part>
    </MainProvision>
  </LawBody>
</Law>"""


def test_parse_multi_hierarchy_resets_lower_levels(multi_hierarchy_xml: str):
    parsed = parse_law_xml(multi_hierarchy_xml, law_id="505AC0000000100")
    assert len(parsed.articles) == 3

    art1 = parsed.articles[0]
    assert art1.part == "第一編　総則"
    assert art1.chapter == "第一章　目的及び定義"
    assert art1.section == "第一節　目的"
    assert (
        art1.hierarchy_path
        == "階層テスト法 > 第一編　総則 > 第一章　目的及び定義 > 第一節　目的 > 第一条（目的）"
    )

    art2 = parsed.articles[1]
    assert art2.part == "第一編　総則"
    assert art2.chapter == "第一章　目的及び定義"
    assert art2.section == "第二節　定義"
    assert (
        art2.hierarchy_path
        == "階層テスト法 > 第一編　総則 > 第一章　目的及び定義 > 第二節　定義 > 第二条（定義）"
    )

    # Chapter 2 has no Section, so section must be reset and NOT leak from Section 2 of Chapter 1
    art3 = parsed.articles[2]
    assert art3.part == "第一編　総則"
    assert art3.chapter == "第二章　手続"
    assert art3.section == ""
    assert art3.hierarchy_path == "階層テスト法 > 第一編　総則 > 第二章　手続 > 第三条"


def test_hierarchy_path_in_frontmatter_and_markdown():
    meta = LawMetadata(
        title="階層テスト法", law_id="505AC0000000100", law_num_text="令和五年法律第百号"
    )
    art = ArticleContent(
        article_id="art_001_第一条",
        num="1",
        title="第一条",
        caption="（目的）",
        part="第一編　総則",
        chapter="第一章　総則",
        section="第一節　通則",
        hierarchy_path="階層テスト法 > 第一編　総則 > 第一章　総則 > 第一節　通則 > 第一条（目的）",
    )
    fm = render_article_frontmatter(meta, art)
    expected_path = (
        'hierarchy_path: "階層テスト法 > 第一編　総則 > '
        '第一章　総則 > 第一節　通則 > 第一条（目的）"'
    )
    assert expected_path in fm
    assert 'part: "第一編　総則"' in fm
    assert 'chapter: "第一章　総則"' in fm
    assert 'section: "第一節　通則"' in fm

    md = render_article_markdown(meta, art)
    assert (
        "**階層文脈**: [階層テスト法](../index.md) > 第一編　総則 > 第一章　総則 > 第一節　通則"
        in md
    )
