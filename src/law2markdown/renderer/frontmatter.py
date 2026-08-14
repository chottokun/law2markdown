"""YAML Frontmatter renderer for OKF/Markdown files."""

from law2markdown.models import ArticleContent, LawMetadata


def get_law_resource_url(law_id: str) -> str:
    """Generate canonical e-Gov laws document URL from law_id."""
    if not law_id:
        return "https://laws.e-gov.go.jp"
    return f"https://laws.e-gov.go.jp/document?lawid={law_id}"


def render_article_frontmatter(
    meta: LawMetadata,
    art: ArticleContent,
    timestamp: str = "",
) -> str:
    """Render article frontmatter compliant with OKF v0.2."""
    caption_part = f" {art.caption}" if art.caption else ""
    title_val = f"{meta.title} {art.title}{caption_part}".strip()
    desc_val = f"{meta.title} {art.chapter} {art.title}{caption_part}".strip()
    resource_url = get_law_resource_url(meta.law_id)
    status_val = "draft" if meta.is_unexecuted else "stable"

    lines = [
        "---",
        "type: law_article",
        f'title: "{title_val}"',
        f'description: "{desc_val}"',
        f'resource: "{resource_url}"',
        f'status: "{status_val}"',
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

    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-law"',
            f'    resource: "{resource_url}"',
            f'    title: "{meta.title}"',
            f'    law_id: "{meta.law_id}"',
            f'    law_num: "{meta.law_num_text}"',
        ]
    )

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
    """Render suppl frontmatter compliant with OKF v0.2."""
    title_suffix = "制定時附則" if suppl_type == "main" else "沿革・改正附則一覧"
    title_val = f"{meta.title} {title_suffix}"
    desc_val = f"{meta.title}の{title_suffix}"
    resource_url = get_law_resource_url(meta.law_id)
    status_val = "draft" if meta.is_unexecuted else "stable"

    lines = [
        "---",
        "type: law_suppl",
        f'title: "{title_val}"',
        f'description: "{desc_val}"',
        f'resource: "{resource_url}"',
        f'status: "{status_val}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
    ]
    if meta.title_kana:
        lines.append(f'title_kana: "{meta.title_kana}"')
    if meta.promulgate_date:
        lines.append(f'promulgate_date: "{meta.promulgate_date}"')
    if meta.enforce_date:
        lines.append(f'enforce_date: "{meta.enforce_date}"')
    if meta.is_unexecuted:
        lines.append("is_unexecuted: true")

    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-law"',
            f'    resource: "{resource_url}"',
            f'    title: "{meta.title}"',
            f'    law_id: "{meta.law_id}"',
        ]
    )

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
    """Render appendix frontmatter compliant with OKF v0.2."""
    title_val = f"{meta.title} {title}"
    desc_val = f"{meta.title}の{title}"
    resource_url = get_law_resource_url(meta.law_id)
    status_val = "draft" if meta.is_unexecuted else "stable"

    lines = [
        "---",
        "type: law_appendix",
        f'title: "{title_val}"',
        f'description: "{desc_val}"',
        f'resource: "{resource_url}"',
        f'status: "{status_val}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
    ]
    if meta.title_kana:
        lines.append(f'title_kana: "{meta.title_kana}"')
    if meta.promulgate_date:
        lines.append(f'promulgate_date: "{meta.promulgate_date}"')
    if meta.enforce_date:
        lines.append(f'enforce_date: "{meta.enforce_date}"')
    if meta.is_unexecuted:
        lines.append("is_unexecuted: true")

    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-law"',
            f'    resource: "{resource_url}"',
            f'    title: "{meta.title}"',
            f'    law_id: "{meta.law_id}"',
        ]
    )

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
    """Render individual law index.md frontmatter compliant with OKF v0.2."""
    resource_url = get_law_resource_url(meta.law_id)
    status_val = "draft" if meta.is_unexecuted else "stable"

    lines = [
        "---",
        "type: law_index",
        f'title: "{meta.title}"',
        f'description: "{meta.title}（{meta.law_num_text}）の目次・条文一覧"',
        f'resource: "{resource_url}"',
        f'status: "{status_val}"',
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

    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-law"',
            f'    resource: "{resource_url}"',
            f'    title: "{meta.title}"',
            f'    law_id: "{meta.law_id}"',
        ]
    )

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
    """Render bundle root index.md frontmatter compliant with OKF v0.2."""
    lines = [
        "---",
        "type: root_index",
        f'title: "{title}"',
        'description: "e-Gov法令データから生成された法令ナレッジベースのルートポータル"',
        'resource: "https://laws.e-gov.go.jp"',
        'status: "stable"',
    ]
    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-portal"',
            '    resource: "https://laws.e-gov.go.jp"',
            '    title: "e-Gov 法令検索"',
        ]
    )

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
    """Render sub-directory index.md frontmatter compliant with OKF v0.2."""
    sub_titles = {
        "articles": "条文一覧",
        "suppl": "附則一覧",
        "appendix": "別表・様式一覧",
    }
    sub_title = sub_titles.get(sub_name, sub_name)
    resource_url = get_law_resource_url(meta.law_id)
    status_val = "draft" if meta.is_unexecuted else "stable"

    lines = [
        "---",
        "type: law_sub_index",
        f'title: "{meta.title} {sub_title}"',
        f'description: "{meta.title}の{sub_title}"',
        f'resource: "{resource_url}"',
        f'status: "{status_val}"',
        f'law_num: "{meta.law_num_text}"',
        f'law_id: "{meta.law_id}"',
    ]
    if meta.title_kana:
        lines.append(f'title_kana: "{meta.title_kana}"')
    if meta.promulgate_date:
        lines.append(f'promulgate_date: "{meta.promulgate_date}"')
    if meta.enforce_date:
        lines.append(f'enforce_date: "{meta.enforce_date}"')
    if meta.is_unexecuted:
        lines.append("is_unexecuted: true")

    if timestamp:
        lines.append("generated:")
        lines.append('  by: "process:law2markdown"')
        lines.append(f'  at: "{timestamp}"')

    lines.extend(
        [
            "sources:",
            '  - id: "egov-law"',
            f'    resource: "{resource_url}"',
            f'    title: "{meta.title}"',
            f'    law_id: "{meta.law_id}"',
        ]
    )

    lines.extend(
        [
            "tags:",
            "  - law_sub_index",
            f"  - {sub_name}",
            "---",
        ]
    )
    return "\n".join(lines)
