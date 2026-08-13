"""Main converter orchestrator for law2markdown."""

import datetime
import re
import zipfile
from pathlib import Path

from law2markdown.models import AppdxContent
from law2markdown.parser.xml_parser import parse_law_xml
from law2markdown.renderer.frontmatter import render_article_frontmatter, render_index_frontmatter
from law2markdown.renderer.markdown import (
    render_appdx_styles_markdown,
    render_article_markdown,
    render_index_markdown,
    render_suppl_amendments_markdown,
    render_suppl_markdown,
)


def convert_law_xml_content(
    xml_content: str,
    output_dir: str,
    law_id: str = "",
) -> Path:
    """Convert XML string content to human-readable Markdown bundle."""
    parsed = parse_law_xml(xml_content, law_id=law_id)
    meta = parsed.metadata

    target_law_id = law_id or meta.law_id or "unknown_law"
    meta.law_id = target_law_id

    # Human readable dir name: {LawTitle}_{law_id} or just {law_id} if no title
    clean_law_title = re.sub(r"[^\w\u3000-\u30fe\u4e00-\u9fa5]", "", meta.title)
    if len(clean_law_title) > 30:
        clean_law_title = clean_law_title[:30] + "…"

    dir_name = f"{clean_law_title}_{target_law_id}" if clean_law_title else target_law_id

    base_path = Path(output_dir) / dir_name
    articles_path = base_path / "articles"
    suppl_path = base_path / "suppl"
    appendix_path = base_path / "appendix"

    articles_path.mkdir(parents=True, exist_ok=True)

    iso_timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    # 1. Export Articles
    for art in parsed.articles:
        art_file = articles_path / f"{art.article_id}.md"
        fm = render_article_frontmatter(meta, art, timestamp=iso_timestamp)
        body = render_article_markdown(meta, art)
        art_file.write_text(f"{fm}\n\n{body}\n", encoding="utf-8")

    # 2. Export SupplProvisions (Aggregated into max 2 files: main & amendments)
    has_suppl_main = False
    has_suppl_amendments = False

    if parsed.suppl_provisions:
        suppl_path.mkdir(parents=True, exist_ok=True)
        main_suppl = None
        amendment_suppls = []

        for suppl in parsed.suppl_provisions:
            if not suppl.amend_law_num and main_suppl is None:
                main_suppl = suppl
            else:
                amendment_suppls.append(suppl)

        if main_suppl is not None:
            has_suppl_main = True
            s_file = suppl_path / "suppl_main.md"
            body = render_suppl_markdown(meta, main_suppl)
            s_file.write_text(f"{body}\n", encoding="utf-8")

        if amendment_suppls:
            has_suppl_amendments = True
            s_file = suppl_path / "suppl_amendments.md"
            body = render_suppl_amendments_markdown(meta, amendment_suppls)
            s_file.write_text(f"{body}\n", encoding="utf-8")

    # 3. Export Appendices
    # Tables remain independent 1-file, Styles/Figs/etc. are aggregated into appdx_styles.md
    table_appendices: list[AppdxContent] = []
    style_appendices: list[AppdxContent] = []

    for app in parsed.appendices:
        if app.appdx_type == "table":
            table_appendices.append(app)
        else:
            style_appendices.append(app)

    if table_appendices:
        appendix_path.mkdir(parents=True, exist_ok=True)
        for app in table_appendices:
            app_file = appendix_path / f"{app.appdx_id}.md"
            app_file.write_text(f"# {app.title}\n\n{app.body}\n", encoding="utf-8")

    has_style_appendices = False
    if style_appendices:
        appendix_path.mkdir(parents=True, exist_ok=True)
        has_style_appendices = True
        app_file = appendix_path / "appdx_styles.md"
        body = render_appdx_styles_markdown(meta, style_appendices)
        app_file.write_text(f"{body}\n", encoding="utf-8")

    # 4. Export index.md
    index_file = base_path / "index.md"
    index_fm = render_index_frontmatter(meta, timestamp=iso_timestamp)
    index_body = render_index_markdown(
        meta=meta,
        articles=parsed.articles,
        has_suppl_main=has_suppl_main,
        has_suppl_amendments=has_suppl_amendments,
        table_appendices=table_appendices,
        has_style_appendices=has_style_appendices,
    )
    index_file.write_text(f"{index_fm}\n\n{index_body}\n", encoding="utf-8")

    return base_path


def convert_law_xml_file(xml_path: str, output_dir: str, law_id: str = "") -> Path:
    """Convert a single XML file."""
    path = Path(xml_path)
    content = path.read_text(encoding="utf-8")

    target_law_id = law_id
    if not target_law_id:
        target_law_id = path.stem

    return convert_law_xml_content(content, output_dir, law_id=target_law_id)


def convert_law_zip_file(zip_path: str, output_dir: str) -> list[Path]:
    """Convert all XML files inside a ZIP archive."""
    zpath = Path(zip_path)
    output_paths: list[Path] = []

    with zipfile.ZipFile(zpath, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                path_obj = Path(name)
                law_id = path_obj.parent.name or path_obj.stem
                xml_bytes = zf.read(name)
                xml_content = xml_bytes.decode("utf-8")
                out_path = convert_law_xml_content(xml_content, output_dir, law_id=law_id)
                output_paths.append(out_path)

    return output_paths
