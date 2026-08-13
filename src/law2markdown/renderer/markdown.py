"""Markdown body renderer for Law articles, index, and suppl."""

from law2markdown.models import (
    AppdxContent,
    ArticleContent,
    ItemContent,
    LawMetadata,
    ParagraphContent,
    SupplProvisionContent,
)
from law2markdown.renderer.table import render_table


def render_item(item: ItemContent, indent_level: int = 1) -> str:
    """Render ItemContent recursively."""
    indent = "  " * indent_level
    lines = []

    body = " ".join(item.sentences)
    lines.append(f"{indent}* **{item.title}** {body}".rstrip())

    for tbl in item.tables:
        lines.append("\n" + render_table(tbl) + "\n")

    for sub in item.subitems:
        lines.append(render_item(sub, indent_level=indent_level + 1))

    return "\n".join(lines)


def render_paragraph(p: ParagraphContent) -> str:
    """Render ParagraphContent."""
    lines = []
    body = " ".join(p.sentences)

    if p.num:
        lines.append(f"**（{p.num}）** {body}".rstrip())
    else:
        if body:
            lines.append(body)

    for tbl in p.tables:
        lines.append("\n" + render_table(tbl) + "\n")

    for item in p.items:
        lines.append(render_item(item, indent_level=1))

    return "\n".join(lines)


def render_article_markdown(meta: LawMetadata, art: ArticleContent) -> str:
    """Render ArticleContent to Markdown body."""
    lines = []

    if art.caption:
        lines.append(f"### {art.caption}")

    lines.append(f"# {art.title}\n")

    # Breadcrumbs
    raw_parts = [art.part, art.chapter, art.section, art.subsection, art.division]
    path_parts = [p for p in raw_parts if p]
    hierarchy_str = " > ".join(path_parts) if path_parts else "本則"
    lines.append(f"**階層文脈**: [{meta.title}](../index.md) > {hierarchy_str}\n")

    for p in art.paragraphs:
        lines.append(render_paragraph(p))
        lines.append("")

    return "\n".join(lines).strip()


def render_suppl_markdown(meta: LawMetadata, suppl: SupplProvisionContent) -> str:
    """Render SupplProvisionContent to Markdown body."""
    lines = [f"# {suppl.label}"]

    if suppl.amend_law_num:
        lines.append(f"**改正法令**: {suppl.amend_law_num}\n")

    lines.append(f"**階層文脈**: [{meta.title}](../index.md) > 附則\n")

    for art in suppl.articles:
        lines.append(f"## {art.title}")
        if art.caption:
            lines.append(f"*{art.caption}*")
        for p in art.paragraphs:
            lines.append(render_paragraph(p))
            lines.append("")

    for p in suppl.paragraphs:
        lines.append(render_paragraph(p))
        lines.append("")

    return "\n".join(lines).strip()


def render_suppl_amendments_markdown(
    meta: LawMetadata, suppl_list: list[SupplProvisionContent]
) -> str:
    """Render all amendment SupplProvisions into a single structured Markdown."""
    lines = [f"# {meta.title} 沿革・改正附則一覧\n"]
    lines.append(f"**階層文脈**: [{meta.title}](../index.md) > 沿革・改正附則一覧\n")

    for s in suppl_list:
        header = f"## {s.label}"
        if s.amend_law_num:
            header += f" （{s.amend_law_num}）"
        lines.append(header + "\n")

        for art in s.articles:
            lines.append(f"### {art.title}")
            if art.caption:
                lines.append(f"*{art.caption}*")
            for p in art.paragraphs:
                lines.append(render_paragraph(p))
                lines.append("")

        for p in s.paragraphs:
            lines.append(render_paragraph(p))
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines).strip()


def render_index_markdown(
    meta: LawMetadata,
    articles: list[ArticleContent],
    has_suppl_main: bool,
    has_suppl_amendments: bool,
    appendices: list[AppdxContent],
) -> str:
    """Render index.md body (Table of Contents with Article Captions)."""
    lines = [f"# {meta.title}\n", "## 目次（条文一覧）\n"]

    current_chapter = ""
    for art in articles:
        if art.chapter and art.chapter != current_chapter:
            current_chapter = art.chapter
            lines.append(f"\n### {current_chapter}\n")

        link_text = f"{art.title}{art.caption}" if art.caption else art.title
        link_str = f"[{link_text}](./articles/{art.article_id}.md)"
        lines.append(f"* {link_str}")

    if has_suppl_main or has_suppl_amendments:
        lines.append("\n## 附則\n")
        if has_suppl_main:
            lines.append("* [制定時附則](./suppl/suppl_main.md)")
        if has_suppl_amendments:
            lines.append("* [沿革・改正附則一覧](./suppl/suppl_amendments.md)")

    if appendices:
        lines.append("\n## 別表・様式一覧\n")
        for app in appendices:
            link_str = f"[{app.title}](./appendix/{app.appdx_id}.md)"
            lines.append(f"* {link_str}")

    return "\n".join(lines).strip()
