"""Tests for law2markdown CLI."""

from pathlib import Path
from unittest.mock import patch

from law2markdown.cli import main


def test_cli_convert_single_xml(tmp_path: Path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="1" Num="1" LawType="Act" Lang="ja">
  <LawNum>令和一年法律第一号</LawNum>
  <LawBody>
    <LawTitle>CLIテスト法</LawTitle>
    <MainProvision>
      <Paragraph Num="1">
        <ParagraphNum/>
        <ParagraphSentence>
          <Sentence>CLIテスト本文。</Sentence>
        </ParagraphSentence>
      </Paragraph>
    </MainProvision>
  </LawBody>
</Law>"""
    xml_path = tmp_path / "test.xml"
    xml_path.write_text(xml_content, encoding="utf-8")
    out_dir = tmp_path / "out"

    test_args = ["law2md", "convert", str(xml_path), "-o", str(out_dir)]
    with patch("sys.argv", test_args):
        ret_code = main()
        assert ret_code == 0

    assert (out_dir / "CLIテスト法" / "index.md").exists()


def test_cli_query_command(tmp_path: Path, capsys):
    from law2markdown.converter import convert_law_xml_content

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Reiwa" Year="1" Num="1" LawType="Act" Lang="ja">
  <LawNum>令和一年法律第一号</LawNum>
  <LawBody>
    <LawTitle>クエリ法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphNum/>
          <ParagraphSentence>
            <Sentence>クエリテスト本文です。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""
    convert_law_xml_content(xml_content, str(tmp_path))

    test_args = ["law2md", "query", "get-article", "クエリ法", "1", "-d", str(tmp_path)]
    with patch("sys.argv", test_args):
        ret_code = main()
        assert ret_code == 0
    captured = capsys.readouterr()
    assert "クエリテスト本文です。" in captured.out
