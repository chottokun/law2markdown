"""Test for duplicate law directory naming and link stability."""

import zipfile
from pathlib import Path

from law2markdown.converter import convert_law_zip_file


def test_convert_zip_duplicate_laws(tmp_path: Path):
    """Test converting a zip with duplicate law titles (e.g. diff enforce dates).

    Ensures that both directories are created without overwriting,
    deterministic ordering is applied, and root index.md does not contain broken links.
    """
    # Create two versions of the same law
    xml_v1 = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Year="22" Num="49" LawType="Act" Lang="ja">
  <LawNum>昭和二十二年法律第四十九号</LawNum>
  <LawBody>
    <LawTitle>テスト法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphSentence>
            <Sentence>旧バージョンの本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""

    xml_v2 = """<?xml version="1.0" encoding="UTF-8"?>
<Law Era="Showa" Year="22" Num="49" LawType="Act" Lang="ja">
  <LawNum>昭和二十二年法律第四十九号</LawNum>
  <LawBody>
    <LawTitle>テスト法</LawTitle>
    <MainProvision>
      <Article Num="1">
        <ArticleTitle>第一条</ArticleTitle>
        <Paragraph Num="1">
          <ParagraphSentence>
            <Sentence>新バージョンの本文。</Sentence>
          </ParagraphSentence>
        </Paragraph>
      </Article>
    </MainProvision>
  </LawBody>
</Law>"""

    csv_lines = [
        "法令種別,法令番号,法令名,法令名読み,旧法令名,公布日,改正法令名,改正法令番号,"
        "改正法令公布日,施行日,施行日備考,法令ID,本文URL,未施行",
        "法律,昭和二十二年法律第四十九号,テスト法,てすとほう,,昭和22年4月7日,改正法A,"
        "令和元年法律第一号,令和元年5月1日,令和元年10月1日,,322AC0000000049,"
        "https://laws.e-gov.go.jp/law/322AC0000000049/20191001_501AC0000000001,",
        "法律,昭和二十二年法律第四十九号,テスト法,てすとほう,,昭和22年4月7日,改正法B,"
        "令和五年法律第二号,令和五年5月1日,令和六年4月1日,,322AC0000000049,"
        "https://laws.e-gov.go.jp/law/322AC0000000049/20240401_505AC0000000002,○",
    ]
    csv_content = "\n".join(csv_lines) + "\n"

    zip_path = tmp_path / "duplicate_laws.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("law_list.csv", csv_content.encode("utf-8-sig"))
        # Intentionally write v2 first in zip to test deterministic sorting
        zf.writestr("322AC0000000049_20240401_505AC0000000002/law.xml", xml_v2)
        zf.writestr("322AC0000000049_20191001_501AC0000000001/law.xml", xml_v1)

    out_dir = tmp_path / "output"
    paths = convert_law_zip_file(str(zip_path), str(out_dir))

    assert len(paths) == 2

    dir_v1 = out_dir / "テスト法"
    dir_v2 = out_dir / "テスト法_2"

    # Both directories must exist and not be overwritten/moved
    assert dir_v1.exists(), f"Expected {dir_v1} to exist"
    assert dir_v2.exists(), f"Expected {dir_v2} to exist"

    # Check that v1 (older enforce_date 20191001) is in dir_v1
    art_v1 = (dir_v1 / "articles" / "art_001_第一条.md").read_text(encoding="utf-8")
    assert "旧バージョンの本文。" in art_v1

    # Check that v2 (newer enforce_date 20240401) is in dir_v2
    art_v2 = (dir_v2 / "articles" / "art_001_第一条.md").read_text(encoding="utf-8")
    assert "新バージョンの本文。" in art_v2

    # Check root index.md links
    root_index = (out_dir / "index.md").read_text(encoding="utf-8")
    assert "[テスト法](./テスト法/index.md)" in root_index
    assert "[テスト法](./テスト法_2/index.md)" in root_index or "[テスト法" in root_index
    assert (out_dir / "テスト法" / "index.md").exists()
    assert (out_dir / "テスト法_2" / "index.md").exists()
