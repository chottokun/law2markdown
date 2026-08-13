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


def render_appdx_styles_markdown(meta: LawMetadata, style_appendices: list[AppdxContent]) -> str:
    """Render all style/fig/note appendices into a single aggregated Markdown."""
    lines = [f"# {meta.title} 様式・その他付録一覧\n"]
    lines.append(f"**階層文脈**: [{meta.title}](../index.md) > 様式・その他付録一覧\n")

    for app in style_appendices:
        lines.append(f"## {app.title}\n")
        lines.append(app.body + "\n")
        lines.append("---\n")

    return "\n".join(lines).strip()


def render_index_markdown(
    meta: LawMetadata,
    articles: list[ArticleContent],
    has_suppl_main: bool,
    has_suppl_amendments: bool,
    table_appendices: list[AppdxContent],
    has_style_appendices: bool,
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

    if table_appendices:
        lines.append("\n## 別表一覧\n")
        for app in table_appendices:
            link_str = f"[{app.title}](./appendix/{app.appdx_id}.md)"
            lines.append(f"* {link_str}")

    if has_style_appendices:
        lines.append("\n## 様式・その他付録\n")
        lines.append("* [様式・その他付録一覧](./appendix/appdx_styles.md)")

    return "\n".join(lines).strip()


def render_root_index_markdown(
    laws_list: list[dict[str, str]],
    title: str = "e-Gov 法令ナレッジベース",
) -> str:
    """Render root index.md body linking to all processed laws."""
    lines = [f"# {title}\n", f"## 収録法令一覧 ({len(laws_list)} 件)\n"]

    grouped: dict[str, list[dict[str, str]]] = {}
    for law in laws_list:
        l_type = law.get("law_type_name", "その他")
        grouped.setdefault(l_type, []).append(law)

    type_order = ["法律", "政令", "勅令", "府省令", "省令", "規則", "その他"]
    sorted_types = sorted(
        grouped.keys(),
        key=lambda t: type_order.index(t) if t in type_order else 99,
    )

    for l_type in sorted_types:
        lines.append(f"### {l_type}\n")
        for law in grouped[l_type]:
            dir_name = law["dir_name"]
            t_name = law["title"]
            num_str = f" ({law['law_num']})" if law.get("law_num") else ""
            unexec = " [未施行]" if law.get("is_unexecuted") else ""
            lines.append(f"* [{t_name}](./{dir_name}/index.md){num_str}{unexec}")
        lines.append("")

    return "\n".join(lines).strip()


def render_articles_index_markdown(meta: LawMetadata, articles: list[ArticleContent]) -> str:
    """Render articles/index.md body."""
    lines = [
        f"# {meta.title} 条文一覧\n",
        f"**階層文脈**: [{meta.title}](../index.md) > 条文一覧\n",
    ]
    current_chapter = ""
    for art in articles:
        if art.chapter and art.chapter != current_chapter:
            current_chapter = art.chapter
            lines.append(f"\n### {current_chapter}\n")

        link_text = f"{art.title}{art.caption}" if art.caption else art.title
        lines.append(f"* [{link_text}](./{art.article_id}.md)")

    return "\n".join(lines).strip()


def render_suppl_index_markdown(meta: LawMetadata, has_main: bool, has_amendments: bool) -> str:
    """Render suppl/index.md body."""
    lines = [
        f"# {meta.title} 附則一覧\n",
        f"**階層文脈**: [{meta.title}](../index.md) > 附則一覧\n",
    ]
    if has_main:
        lines.append("* [制定時附則](./suppl_main.md)")
    if has_amendments:
        lines.append("* [沿革・改正附則一覧](./suppl_amendments.md)")

    return "\n".join(lines).strip()


def render_appendix_index_markdown(
    meta: LawMetadata,
    table_appendices: list[AppdxContent],
    has_style_appendices: bool,
) -> str:
    """Render appendix/index.md body."""
    lines = [
        f"# {meta.title} 別表・様式一覧\n",
        f"**階層文脈**: [{meta.title}](../index.md) > 別表・様式一覧\n",
    ]
    if table_appendices:
        lines.append("## 別表一覧\n")
        for app in table_appendices:
            lines.append(f"* [{app.title}](./{app.appdx_id}.md)")

    if has_style_appendices:
        lines.append("\n## 様式・その他付録\n")
        lines.append("* [様式・その他付録一覧](./appdx_styles.md)")

    return "\n".join(lines).strip()
