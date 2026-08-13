"""Main converter orchestrator for law2markdown."""

import datetime
import re
import zipfile
from pathlib import Path
from typing import Any

from law2markdown.models import AppdxContent, LawMetadata
from law2markdown.parser.csv_parser import parse_law_csv_content
from law2markdown.parser.xml_parser import parse_law_xml
from law2markdown.renderer.frontmatter import (
    render_appdx_frontmatter,
    render_article_frontmatter,
    render_index_frontmatter,
    render_root_index_frontmatter,
    render_suppl_frontmatter,
)
from law2markdown.renderer.markdown import (
    render_appdx_styles_markdown,
    render_article_markdown,
    render_index_markdown,
    render_root_index_markdown,
    render_suppl_amendments_markdown,
    render_suppl_markdown,
)


def convert_law_xml_content_with_meta(
    xml_content: str,
    output_dir: str,
    law_id: str = "",
    extra_metadata: dict[str, Any] | None = None,
) -> tuple[Path, LawMetadata]:
    """Convert XML content and return Path and LawMetadata."""
    parsed = parse_law_xml(xml_content, law_id=law_id)
    meta = parsed.metadata

    if extra_metadata:
        if not meta.title_kana and extra_metadata.get("title_kana"):
            meta.title_kana = extra_metadata["title_kana"]
        if extra_metadata.get("promulgate_date"):
            meta.promulgate_date = extra_metadata["promulgate_date"]
        if extra_metadata.get("enforce_date"):
            meta.enforce_date = extra_metadata["enforce_date"]
        if extra_metadata.get("amend_law_title"):
            meta.amend_law_title = extra_metadata["amend_law_title"]
        if extra_metadata.get("amend_law_num"):
            meta.amend_law_num = extra_metadata["amend_law_num"]
        if extra_metadata.get("is_unexecuted") is not None:
            meta.is_unexecuted = extra_metadata["is_unexecuted"]

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
            fm = render_suppl_frontmatter(meta, "main", timestamp=iso_timestamp)
            body = render_suppl_markdown(meta, main_suppl)
            s_file.write_text(f"{fm}\n\n{body}\n", encoding="utf-8")

        if amendment_suppls:
            has_suppl_amendments = True
            s_file = suppl_path / "suppl_amendments.md"
            fm = render_suppl_frontmatter(meta, "amendments", timestamp=iso_timestamp)
            body = render_suppl_amendments_markdown(meta, amendment_suppls)
            s_file.write_text(f"{fm}\n\n{body}\n", encoding="utf-8")

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
            fm = render_appdx_frontmatter(meta, app.title, app.appdx_type, timestamp=iso_timestamp)
            app_file.write_text(f"{fm}\n\n# {app.title}\n\n{app.body}\n", encoding="utf-8")

    has_style_appendices = False
    if style_appendices:
        appendix_path.mkdir(parents=True, exist_ok=True)
        has_style_appendices = True
        app_file = appendix_path / "appdx_styles.md"
        fm = render_appdx_frontmatter(
            meta, "様式・その他付録一覧", "style", timestamp=iso_timestamp
        )
        body = render_appdx_styles_markdown(meta, style_appendices)
        app_file.write_text(f"{fm}\n\n{body}\n", encoding="utf-8")

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

    return base_path, meta


def convert_law_xml_content(
    xml_content: str,
    output_dir: str,
    law_id: str = "",
    extra_metadata: dict[str, Any] | None = None,
) -> Path:
    """Convert XML string content to human-readable Markdown bundle."""
    path, _ = convert_law_xml_content_with_meta(
        xml_content, output_dir, law_id=law_id, extra_metadata=extra_metadata
    )
    return path


def convert_law_xml_file(xml_path: str, output_dir: str, law_id: str = "") -> Path:
    """Convert a single XML file."""
    path = Path(xml_path)
    content = path.read_text(encoding="utf-8")

    target_law_id = law_id
    if not target_law_id:
        target_law_id = path.stem

    return convert_law_xml_content(content, output_dir, law_id=target_law_id)


def convert_law_zip_file(zip_path: str, output_dir: str) -> list[Path]:
    """Convert all XML files inside a ZIP archive with CSV metadata enrichment."""
    zpath = Path(zip_path)
    output_paths: list[Path] = []
    csv_map: dict[str, dict[str, Any]] = {}
    processed_laws: list[dict[str, Any]] = []

    with zipfile.ZipFile(zpath, "r") as zf:
        # 1. First pass: read CSV metadata if available
        for name in zf.namelist():
            if name.endswith(".csv"):
                try:
                    csv_bytes = zf.read(name)
                    csv_text = csv_bytes.decode("utf-8-sig", errors="replace")
                    csv_map.update(parse_law_csv_content(csv_text))
                except Exception:
                    pass

        # 2. Second pass: process XML files
        for name in zf.namelist():
            if name.endswith(".xml"):
                path_obj = Path(name)
                law_id = path_obj.parent.name or path_obj.stem
                xml_bytes = zf.read(name)
                xml_content = xml_bytes.decode("utf-8", errors="replace")

                extra_meta = csv_map.get(law_id, {})
                out_path, parsed_meta = convert_law_xml_content_with_meta(
                    xml_content,
                    output_dir,
                    law_id=law_id,
                    extra_metadata=extra_meta,
                )
                output_paths.append(out_path)

                # Law summary for root index
                law_type_map = {
                    "Act": "法律",
                    "CabinetOrder": "政令",
                    "ImperialOrder": "勅令",
                    "MinisterialOrdinance": "府省令",
                    "Rule": "規則",
                    "Constitution": "憲法",
                }
                law_type_name = extra_meta.get("law_type") or law_type_map.get(
                    parsed_meta.law_type, "その他"
                )
                processed_laws.append(
                    {
                        "dir_name": out_path.name,
                        "title": parsed_meta.title,
                        "law_num": parsed_meta.law_num_text,
                        "law_type_name": law_type_name,
                        "is_unexecuted": parsed_meta.is_unexecuted,
                    }
                )

    # 3. Export Root index.md
    if processed_laws:
        root_index_path = Path(output_dir) / "index.md"
        iso_timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        r_fm = render_root_index_frontmatter(timestamp=iso_timestamp)
        r_body = render_root_index_markdown(processed_laws)
        root_index_path.write_text(f"{r_fm}\n\n{r_body}\n", encoding="utf-8")

    return output_paths
