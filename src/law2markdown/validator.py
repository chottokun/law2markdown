"""Link integrity validator for generated markdown files."""

import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationReport:
    """Validation report for markdown links and statistics."""

    total_files_checked: int = 0
    total_links_checked: int = 0
    broken_links: list[tuple[str, str, str]] = field(default_factory=list)  # (file, target, reason)
    total_laws: int = 0
    total_articles: int = 0
    total_suppls: int = 0
    total_appendices: int = 0

    @property
    def is_valid(self) -> bool:
        """Return True if no broken links found."""
        return len(self.broken_links) == 0


def validate_directory_links(root_dir: str | Path) -> ValidationReport:
    """Validate all relative markdown links within root_dir."""
    root_path = Path(root_dir)
    report = ValidationReport()

    if not root_path.exists():
        report.broken_links.append((str(root_path), "", "Directory does not exist"))
        return report

    # Regex to find markdown links: [text](link) excluding external URLs or anchor-only links
    link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

    for md_file in root_path.rglob("*.md"):
        report.total_files_checked += 1
        rel_file_path = md_file.relative_to(root_path)

        # Count file categories
        if md_file.parent.name == "articles" and md_file.name != "index.md":
            report.total_articles += 1
        elif md_file.parent.name == "suppl" and md_file.name != "index.md":
            report.total_suppls += 1
        elif md_file.parent.name == "appendix" and md_file.name != "index.md":
            report.total_appendices += 1
        elif md_file.name == "index.md" and md_file.parent != root_path:
            if md_file.parent.name not in ("articles", "suppl", "appendix"):
                report.total_laws += 1

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            report.broken_links.append((str(rel_file_path), "", f"Read error: {e}"))
            continue

        for match in link_pattern.finditer(content):
            raw_target = match.group(2).strip()

            # Skip external links, mailto, etc.
            if raw_target.startswith(("http://", "https://", "mailto:", "ftp://")):
                continue

            # Remove optional anchor and url decode
            target_path_part = raw_target.split("#")[0].strip()
            if not target_path_part:
                continue

            target_decoded = urllib.parse.unquote(target_path_part)
            report.total_links_checked += 1

            # Resolve target relative to current md_file's parent directory
            resolved_target = (md_file.parent / target_decoded).resolve()

            if not resolved_target.exists():
                report.broken_links.append(
                    (str(rel_file_path), raw_target, "Target file does not exist")
                )

    return report
