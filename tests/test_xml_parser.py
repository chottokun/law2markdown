"""Tests for XML parser."""

import pytest

from law2markdown.parser.xml_parser import parse_law_xml


@pytest.fixture
def simple_law_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Year="22" Num="49" LawType="Act" Lang="ja">
  <LawNum>昭和二十二年法律第四十九号</LawNum>
  <LawBody>
    <LawTitle Kana="ろうどうきじゅんほう">労働基準法</LawTitle>
    <MainProvision>
      <Chapter Num="1">
        <ChapterTitle>第一章　総則</ChapterTitle>
        <Article Num="1">
          <ArticleCaption>（労働条件の原則）</ArticleCaption>
          <ArticleTitle>第一条</ArticleTitle>
          <Paragraph Num="1">
            <ParagraphNum/>
            <ParagraphSentence>
              <Sentence>労働条件は、労働者が人たるに値する生活を営むための必要を満たすものでなければならない。</Sentence>
            </ParagraphSentence>
          </Paragraph>
          <Paragraph Num="2">
            <ParagraphNum>２</ParagraphNum>
            <ParagraphSentence>
              <Sentence>この法律で定める労働条件の基準は最低のものであるから、労働関係の当事者は、この基準を理由として労働条件を低下させてはならない。</Sentence>
            </ParagraphSentence>
          </Paragraph>
        </Article>
        <Article Num="2">
          <ArticleTitle>第二条</ArticleTitle>
          <Paragraph Num="1">
            <ParagraphNum/>
            <ParagraphSentence>
              <Sentence>労働条件は、労働者と使用者が、対等の立場において決定すべきものである。</Sentence>
            </ParagraphSentence>
          </Paragraph>
        </Article>
      </Chapter>
    </MainProvision>
    <SupplProvision>
      <SupplProvisionLabel>附　則</SupplProvisionLabel>
      <Paragraph Num="1">
        <ParagraphNum/>
        <ParagraphSentence>
          <Sentence>この法律は、昭和二十二年九月一日から施行する。</Sentence>
        </ParagraphSentence>
      </Paragraph>
    </SupplProvision>
  </LawBody>
</Law>"""


def test_parse_simple_law(simple_law_xml):
    parsed = parse_law_xml(simple_law_xml, law_id="322AC0000000049")
    meta = parsed.metadata
    assert meta.era == "Showa"
    assert meta.year == 22
    assert meta.num == 49
    assert meta.law_type == "Act"
    assert meta.law_num_text == "昭和二十二年法律第四十九号"
    assert meta.title == "労働基準法"
    assert meta.title_kana == "ろうどうきじゅんほう"
    assert meta.law_id == "322AC0000000049"

    assert len(parsed.articles) == 2
    art1 = parsed.articles[0]
    assert art1.article_id == "art_001"
    assert art1.num == "1"
    assert art1.title == "第一条"
    assert art1.caption == "（労働条件の原則）"
    assert art1.chapter == "第一章　総則"
    assert len(art1.paragraphs) == 2
    p1_text = art1.paragraphs[0].sentences[0]
    expected_p1 = (
        "労働条件は、労働者が人たるに値する生活を営むための必要を満たすものでなければならない。"
    )
    assert p1_text == expected_p1
    assert art1.paragraphs[1].num == "２"

    assert len(parsed.suppl_provisions) == 1
    suppl = parsed.suppl_provisions[0]
    assert suppl.label == "附　則"
    assert len(suppl.paragraphs) == 1


@pytest.fixture
def ruby_and_subitem_xml():
    return """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="1" Num="10" LawType="CabinetOrder" Lang="ja">
  <LawNum>令和元年政令第十号</LawNum>
  <LawBody>
    <LawTitle>テスト政令</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence><Ruby>親文字<Rt>ルビ</Rt></Ruby>のテスト。</Sentence>
          </ParagraphSentence>
          <Item Num="1">
            <ItemTitle>一</ItemTitle>
            <ItemSentence>
              <Sentence>第一号のテキスト。</Sentence>
            </ItemSentence>

            <Subitem1 Num="1">
              <Subitem1Title>イ</Subitem1Title>
              <Subitem1Sentence>
                <Sentence>サブアイテムのテキスト。</Sentence>
              </Subitem1Sentence>
            </Subitem1>
          </Item>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""


def test_parse_ruby_and_subitem(ruby_and_subitem_xml):
    parsed = parse_law_xml(ruby_and_subitem_xml)
    art = parsed.articles[0]
    assert art.paragraphs[0].sentences[0] == "親文字のテスト。"
    item = art.paragraphs[0].items[0]
    assert item.title == "一"
    assert item.sentences[0] == "第一号のテキスト。"
    assert len(item.subitems) == 1
    sub = item.subitems[0]
    assert sub.title == "イ"
    assert sub.sentences[0] == "サブアイテムのテキスト。"
