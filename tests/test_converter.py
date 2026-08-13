"""Tests for law2markdown converter."""

import zipfile
from pathlib import Path

from law2markdown.converter import convert_law_xml_file, convert_law_zip_file


def test_convert_single_xml(tmp_path: Path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Year="22" Num="49" LawType="Act" Lang="ja">
  <LawNum>昭和二十二年法律第四十九号</LawNum>
  <LawBody>
    <LawTitle>テスト法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>テスト本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    out_dir = tmp_path / "output"
    convert_law_xml_file(str(xml_file), str(out_dir), law_id="322AC0000000049")

    law_out_dir = out_dir / "322AC0000000049"
    assert law_out_dir.exists()
    assert (law_out_dir / "index.md").exists()
    assert (law_out_dir / "articles" / "art_001.md").exists()

    index_text = (law_out_dir / "index.md").read_text(encoding="utf-8")
    assert "# テスト法" in index_text
    assert "[第一条](./articles/art_001.md)" in index_text

    art_text = (law_out_dir / "articles" / "art_001.md").read_text(encoding="utf-8")
    assert "type: law_article" in art_text
    assert "テスト本文。" in art_text


def test_convert_zip_file(tmp_path: Path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Heisei" Year="13" Num="318" LawType="CabinetOrder" Lang="ja">
  <LawNum>平成十三年政令第三百十八号</LawNum>
  <LawBody>
    <LawTitle>テスト政令</LawTitle>
    <MainProvision>
      <Paragraph Num="1">
        <ParagraphNum/>
        <ParagraphSentence>
          <Sentence>政令本文。</Sentence>
        </ParagraphSentence>
      </Paragraph>
    </MainProvision>
  </LawBody>
</Law>"""
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("413CO0000000318/413CO0000000318.xml", xml_content)

    out_dir = tmp_path / "output_zip"
    convert_law_zip_file(str(zip_path), str(out_dir))

    law_out = out_dir / "413CO0000000318"
    assert law_out.exists()
    assert (law_out / "index.md").exists()
