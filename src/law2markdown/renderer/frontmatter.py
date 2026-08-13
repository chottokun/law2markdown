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
    ]
    if meta.title_kana:
        lines.append(f'title_kana: "{meta.title_kana}"')
    if meta.promulgate_date:
        lines.append(f'promulgate_date: "{meta.promulgate_date}"')
    if meta.enforce_date:
        lines.append(f'enforce_date: "{meta.enforce_date}"')
    if meta.amend_law_title:
        lines.append(f'amend_law_title: "{meta.amend_law_title}"')
    if meta.amend_law_num:
        lines.append(f'amend_law_num: "{meta.amend_law_num}"')
    if meta.is_unexecuted:
        lines.append("is_unexecuted: true")

    lines.extend(
        [
            "sources:",
            f'  - law_id: "{meta.law_id}"',
            f'    law_num: "{meta.law_num_text}"',
        ]
    )
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
    ]
    if meta.title_kana:
        lines.append(f'title_kana: "{meta.title_kana}"')
    if meta.promulgate_date:
        lines.append(f'promulgate_date: "{meta.promulgate_date}"')
    if meta.enforce_date:
        lines.append(f'enforce_date: "{meta.enforce_date}"')
    if meta.amend_law_title:
        lines.append(f'amend_law_title: "{meta.amend_law_title}"')
    if meta.amend_law_num:
        lines.append(f'amend_law_num: "{meta.amend_law_num}"')
    if meta.is_unexecuted:
        lines.append("is_unexecuted: true")

    lines.extend(
        [
            "sources:",
            f'  - law_id: "{meta.law_id}"',
        ]
    )
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


def render_root_index_frontmatter(
    title: str = "e-Gov 法令ナレッジベース", timestamp: str = ""
) -> str:
    """Render root index.md frontmatter compliant with OKF."""
    lines = [
        "---",
        "type: root_index",
        f'title: "{title}"',
    ]
    if timestamp:
        lines.append(f'timestamp: "{timestamp}"')

    lines.extend(
        [
            "tags:",
            "  - law_root_index",
            "  - e-gov",
            "---",
        ]
    )
    return "\n".join(lines)


def render_sub_index_frontmatter(
    meta: LawMetadata,
    sub_name: str,  # "articles" | "suppl" | "appendix"
    timestamp: str = "",
) -> str:
    """Render sub-directory index.md frontmatter compliant with OKF."""
    sub_titles = {
        "articles": "条文一覧",
        "suppl": "附則一覧",
        "appendix": "別表・様式一覧",
    }
    sub_title = sub_titles.get(sub_name, sub_name)
    lines = [
        "---",
        "type: law_sub_index",
        f'title: "{meta.title} {sub_title}"',
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
            "  - law_sub_index",
            f"  - {sub_name}",
            "---",
        ]
    )
    return "\n".join(lines)
