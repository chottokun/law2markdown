from typing import Any

from law2markdown.models import (
    AppdxContent,
    ArticleContent,
    ChildAnchor,
    ItemContent,
    LawMetadata,
    ParagraphContent,
    SupplProvisionContent,
)
from law2markdown.renderer.table import render_table


def render_item(
    item: ItemContent, parent_anchor: str = "", item_idx: int = 1, indent_level: int = 1
) -> str:
    """Render ItemContent recursively with anchor."""
    indent = "  " * indent_level
    lines = []

    level_prefix = "s" if indent_level > 1 else "i"
    anchor_id = f"{parent_anchor}-{level_prefix}{item_idx}" if parent_anchor else f"i{item_idx}"
    anchor_tag = f'<a id="{anchor_id}"></a>'

    body = " ".join(item.sentences)
    lines.append(f"{indent}* {anchor_tag}**{item.title}** {body}".rstrip())

    for tbl in item.tables:
        lines.append("\n" + render_table(tbl) + "\n")

    for s_idx, sub in enumerate(item.subitems, start=1):
        lines.append(
            render_item(sub, parent_anchor=anchor_id, item_idx=s_idx, indent_level=indent_level + 1)
        )

    return "\n".join(lines)


def render_paragraph(p: ParagraphContent, p_idx: int = 1) -> str:
    """Render ParagraphContent with anchor."""
    lines = []
    body = " ".join(p.sentences)
    p_id = f"p{p_idx}"
    anchor_tag = f'<a id="{p_id}"></a>'

    if p.num:
        lines.append(f"{anchor_tag}**（{p.num}）** {body}".rstrip())
    else:
        if body:
            lines.append(f"{anchor_tag}{body}".rstrip())
        else:
            lines.append(anchor_tag)

    for tbl in p.tables:
        lines.append("\n" + render_table(tbl) + "\n")

    for i_idx, item in enumerate(p.items, start=1):
        lines.append(render_item(item, parent_anchor=p_id, item_idx=i_idx, indent_level=1))

    return "\n".join(lines)


def render_article_markdown(
    meta: LawMetadata,
    art: ArticleContent,
    articles_map: dict[str, ArticleContent] | None = None,
    appendices_map: dict[str, AppdxContent] | None = None,
    definitions: list[Any] | None = None,
) -> str:
    """Render ArticleContent to Markdown body and populate art.child_anchors."""
    lines = []

    if art.caption:
        lines.append(f"### {art.caption}")

    lines.append(f"# {art.title}\n")

    # Breadcrumbs
    raw_parts = [art.part, art.chapter, art.section, art.subsection, art.division]
    path_parts = [p for p in raw_parts if p]
    hierarchy_str = " > ".join(path_parts) if path_parts else "本則"
    lines.append(f"**階層文脈**: [{meta.title}](../index.md) > {hierarchy_str}\n")

    for p_idx, p in enumerate(art.paragraphs, start=1):
        lines.append(render_paragraph(p, p_idx=p_idx))
        lines.append("")

    raw_body = "\n".join(lines).strip()

    # Calculate child_anchors offsets
    import re

    anchor_pattern = re.compile(r'<a id="([^"]+)"></a>')
    matches = list(anchor_pattern.finditer(raw_body))
    child_anchors: list[ChildAnchor] = []

    for i, m in enumerate(matches):
        a_id = m.group(1)
        start_offset = m.start()
        end_offset = matches[i + 1].start() if i + 1 < len(matches) else len(raw_body)

        # Determine level and label
        if "-s" in a_id:
            level = "subitem"
            label = f"細分 {a_id}"
        elif "-i" in a_id:
            level = "item"
            label = f"号 {a_id}"
        else:
            level = "paragraph"
            p_num = a_id.replace("p", "")
            label = f"第{p_num}項"

        child_anchors.append(
            ChildAnchor(
                id=a_id,
                level=level,
                label=label,
                start_offset=start_offset,
                end_offset=end_offset,
            )
        )

    art.child_anchors = child_anchors

    # Supplemental reference section (ASIS body strictly preserved above)
    has_refs = bool(art.outbound_references or art.inbound_references)
    if has_refs and (articles_map or appendices_map):
        lines.append("\n---")
        lines.append("## 参照・関連規定\n")

        if art.outbound_references:
            lines.append("### 参照条文・付録\n")
            for ref_id in art.outbound_references:
                target_art = articles_map.get(ref_id) if articles_map else None
                if target_art:
                    label = (
                        f"{target_art.title}{target_art.caption}"
                        if target_art.caption
                        else target_art.title
                    )
                    lines.append(f"* [{label}](./{ref_id}.md)")
                elif appendices_map and ref_id in appendices_map:
                    target_app = appendices_map[ref_id]
                    lines.append(f"* [{target_app.title}](../appendix/{ref_id}.md)")
                else:
                    lines.append(f"* [{ref_id}](./{ref_id}.md)")
            lines.append("")

        if art.inbound_references:
            lines.append("### 被参照条文\n")
            for ref_id in art.inbound_references:
                target_art = articles_map.get(ref_id) if articles_map else None
                if target_art:
                    label = (
                        f"{target_art.title}{target_art.caption}"
                        if target_art.caption
                        else target_art.title
                    )
                    lines.append(f"* [{label}](./{ref_id}.md)")
                else:
                    lines.append(f"* [{ref_id}](./{ref_id}.md)")
            lines.append("")

    # Supplemental definition section
    if art.referenced_terms:
        defn_map = {d.term: d for d in definitions} if definitions else {}
        lines.append("\n---")
        lines.append("## 定義用語\n")
        for term in art.referenced_terms:
            d = defn_map.get(term)
            if d and d.article_id:
                target_art = articles_map.get(d.article_id) if articles_map else None
                if target_art and target_art.caption:
                    art_label = f"{target_art.title}{target_art.caption}"
                elif target_art:
                    art_label = target_art.title
                else:
                    art_label = d.article_title or d.article_id
                art_link = f"[{art_label}](./{d.article_id}.md)"
                lines.append(f"* [{term}](../definitions.md#{term}) - 定義条文: {art_link}")
            else:
                lines.append(f"* [{term}](../definitions.md#{term})")
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
    has_definitions: bool = False,
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

    if has_definitions:
        lines.append("\n## 用語定義\n")
        lines.append("* [用語定義レジストリ](./definitions.md)")

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


def render_definitions_markdown(meta: LawMetadata, definitions: list[Any]) -> str:
    """Render definitions.md body."""
    lines = [
        f"# {meta.title} 用語定義レジストリ\n",
        f"**階層文脈**: [{meta.title}](./index.md) > 用語定義レジストリ\n",
        f"本法令（{meta.law_num_text}）における定義規定から抽出された法定用語一覧です。\n",
    ]

    for d in sorted(definitions, key=lambda x: x.term):
        anchor_tag = f'<a id="{d.term}"></a>'
        lines.append(f"## {anchor_tag}{d.term}\n")
        lines.append(f"- **定義文**: {d.definition_text}")
        if d.article_id:
            art_label = d.article_title or d.article_id
            lines.append(f"- **定義条文**: [{art_label}](./articles/{d.article_id}.md)")
        if d.scope:
            lines.append(f"- **適用範囲**: {d.scope}")
        lines.append("\n---\n")

    return "\n".join(lines).strip()
