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

    law_out_dir = out_dir / "テスト法"
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


def test_convert_appendix_with_long_title(tmp_path: Path):
    long_title = (
        "別表第五十五号　１２２ＧＨｚを超え１２７５ＧＨｚ以下の周波数の電波を使用する"
        "衛星基幹放送局を用いて行う狭帯域伝送方式による標準テレビジョン放送及び"
        "高精細度テレビジョン放送のうちデジタル放送の輝度信号及び色差信号の方程式"
    )
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="1" Num="1" LawType="MinisterialOrdinance" Lang="ja">
  <LawNum>令和元年総務省令第一号</LawNum>
  <LawBody>
    <LawTitle>電波テスト府省令</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphSentence>
            <Sentence>本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
    <AppdxTable>
      <AppdxTableTitle>{long_title}</AppdxTableTitle>
      <TableStruct>
        <Table>
          <TableRow>
            <TableColumn><Sentence>方程式の内容</Sentence></TableColumn>
          </TableRow>
        </Table>
      </TableStruct>
    </AppdxTable>
  </LawBody>
</Law>"""
    xml_file = tmp_path / "long_appendix.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    out_dir = tmp_path / "out"
    convert_law_xml_file(str(xml_file), str(out_dir), law_id="501M10000008001")

    law_out = out_dir / "電波テスト府省令"
    assert law_out.exists()
    appendix_dir = law_out / "appendix"
    assert appendix_dir.exists()

    md_files = [f for f in appendix_dir.glob("*.md") if f.name != "index.md"]
    assert len(md_files) == 1
    app_file = md_files[0]

    # Verify filename is within safe limits (< 100 bytes, ext4 limit 255 bytes)
    assert len(app_file.name.encode("utf-8")) < 120
    assert "別表第五十五号" in app_file.name
    assert app_file.read_text(encoding="utf-8")
