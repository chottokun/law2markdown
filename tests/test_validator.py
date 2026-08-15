"""Tests for validator module."""

from pathlib import Path

from law2markdown.validator import validate_directory_links


def test_validator_detects_broken_link(tmp_path: Path):
    # Valid file with invalid link
    f1 = tmp_path / "index.md"
    f1.write_text("[存在しないファイル](./non_existent.md)", encoding="utf-8")

    report = validate_directory_links(tmp_path)
    assert not report.is_valid
    assert len(report.broken_links) == 1
    assert "non_existent.md" in report.broken_links[0][1]


def test_validator_passes_valid_links(tmp_path: Path):
    f1 = tmp_path / "index.md"
    f2 = tmp_path / "target.md"

    f2.write_text("# Target", encoding="utf-8")
    f1.write_text("[リンク](./target.md)", encoding="utf-8")

    report = validate_directory_links(tmp_path)
    assert report.is_valid
    assert report.total_links_checked == 1
    assert report.total_files_checked == 2
