"""Tests for converter module."""

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
        <ArticleCaption>（目的）</ArticleCaption>
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

    law_out_dir = out_dir / "テスト法_322AC0000000049"
    assert law_out_dir.exists()
    assert (law_out_dir / "index.md").exists()
    assert (law_out_dir / "articles" / "art_001_第一条.md").exists()
    assert (law_out_dir / "articles" / "index.md").exists()

    index_text = (law_out_dir / "index.md").read_text(encoding="utf-8")
    assert "# テスト法" in index_text
    assert "[第一条（目的）](./articles/art_001_第一条.md)" in index_text

    art_text = (law_out_dir / "articles" / "art_001_第一条.md").read_text(encoding="utf-8")
    assert "type: law_article" in art_text
    assert "テスト本文。" in art_text


def test_convert_zip_file(tmp_path: Path):
    zip_path = tmp_path / "sample.zip"
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Year="22" Num="49" LawType="Act" Lang="ja">
  <LawNum>昭和二十二年法律第四十九号</LawNum>
  <LawBody>
    <LawTitle>ZIPテスト法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("law1/law1.xml", xml_content)

    out_dir = tmp_path / "zip_output"
    paths = convert_law_zip_file(str(zip_path), str(out_dir))

    assert len(paths) == 1
    assert paths[0].exists()
    assert (out_dir / "index.md").exists()
    root_idx = (out_dir / "index.md").read_text(encoding="utf-8")
    assert "type: root_index" in root_idx
    assert "[ZIPテスト法]" in root_idx
