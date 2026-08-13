"""YAML Frontmatter renderer for OKF/Markdown files."""

from law2markdown.models import ArticleContent, LawMetadata


def render_article_frontmatter(
    meta: LawMetadata,
    art: ArticleContent,
    timestamp: str = "",
) -> str:
    """Render article frontmatter compliant with OKF."""
    lines = [
        "---",
        "type: law_article",
        f'title: "{meta.title} {art.title}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
        f'article_num: "{art.num}"',
        f'chapter: "{art.chapter}"',
        f'section: "{art.section}"',
        "sources:",
        f'  - law_id: "{meta.law_id}"',
        f'    law_num: "{meta.law_num_text}"',
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


def render_suppl_frontmatter(
    meta: LawMetadata,
    suppl_type: str,  # "main" | "amendments"
    timestamp: str = "",
) -> str:
    """Render suppl frontmatter compliant with OKF."""
    title_suffix = "制定時附則" if suppl_type == "main" else "沿革・改正附則一覧"
    lines = [
        "---",
        "type: law_suppl",
        f'title: "{meta.title} {title_suffix}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
        "sources:",
        f'  - law_id: "{meta.law_id}"',
    ]
    if timestamp:
        lines.append(f'timestamp: "{timestamp}"')

    lines.extend(
        [
            "tags:",
            "  - law_suppl",
            f"  - {meta.law_type}",
            "---",
        ]
    )
    return "\n".join(lines)


def render_appdx_frontmatter(
    meta: LawMetadata,
    title: str,
    appdx_type: str,
    timestamp: str = "",
) -> str:
    """Render appendix frontmatter compliant with OKF."""
    lines = [
        "---",
        "type: law_appendix",
        f'title: "{meta.title} {title}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
        "sources:",
        f'  - law_id: "{meta.law_id}"',
    ]
    if timestamp:
        lines.append(f'timestamp: "{timestamp}"')

    lines.extend(
        [
            "tags:",
            "  - law_appendix",
            f"  - {appdx_type}",
            "---",
        ]
    )
    return "\n".join(lines)


def render_index_frontmatter(meta: LawMetadata, timestamp: str = "") -> str:
    """Render index.md frontmatter compliant with OKF."""
    lines = [
        "---",
        "type: law_index",
        f'title: "{meta.title}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
        "sources:",
        f'  - law_id: "{meta.law_id}"',
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
