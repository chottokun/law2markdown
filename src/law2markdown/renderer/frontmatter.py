"""YAML Frontmatter renderer for OKF/Markdown files."""

from law2markdown.models import ArticleContent, LawMetadata


def render_article_frontmatter(
    meta: LawMetadata,
    art: ArticleContent,
    timestamp: str = "",
) -> str:
    """Render article frontmatter."""
    lines = [
        "---",
        "type: law_article",
        f'title: "{meta.title} {art.title}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
        f'article_num: "{art.num}"',
        f'chapter: "{art.chapter}"',
        f'section: "{art.section}"',
    ]
    if timestamp:
        lines.append(f'timestamp: "{timestamp}"')

    lines.extend(
        [
            "tags:",
            "  - law",
            f"  - {meta.law_type}",
            "---",
        ]
    )
    return "\n".join(lines)


def render_index_frontmatter(meta: LawMetadata, timestamp: str = "") -> str:
    """Render index.md frontmatter."""
    lines = [
        "---",
        "type: law_index",
        f'title: "{meta.title}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
    ]
    if timestamp:
        lines.append(f'timestamp: "{timestamp}"')

    lines.extend(
        [
            "tags:",
            "  - law_root",
            f"  - {meta.law_type}",
            "---",
        ]
    )
    return "\n".join(lines)
