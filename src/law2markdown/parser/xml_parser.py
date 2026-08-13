"""e-Gov Law XML Parser."""

import re
from dataclasses import dataclass, field

from lxml import etree

from law2markdown.models import (
    AppdxContent,
    ArticleContent,
    ItemContent,
    LawMetadata,
    ParagraphContent,
    SupplProvisionContent,
    TableCell,
    TableContent,
    TableRow,
)
from law2markdown.renderer.formula import render_formula


@dataclass
class ParsedLawData:
    """Parsed law data structure."""

    metadata: LawMetadata
    articles: list[ArticleContent] = field(default_factory=list)
    suppl_provisions: list[SupplProvisionContent] = field(default_factory=list)
    appendices: list[AppdxContent] = field(default_factory=list)


def clean_text_asis(element: etree._Element | None) -> str:
    """Extract text as-is while removing Ruby reading tags (<Rt>)."""
    if element is None:
        return ""

    text_buf = []

    def _walk(node: etree._Element):
        tag = node.tag if isinstance(node.tag, str) else ""
        if tag == "Rt":
            return
        if tag == "ArithFormula":
            formula_raw = "".join(node.itertext()).strip()
            text_buf.append(render_formula(formula_raw))
            return
        if tag == "Sup":
            text_buf.append("<sup>" + _extract_inner(node) + "</sup>")
            return
        if tag == "Sub":
            text_buf.append("<sub>" + _extract_inner(node) + "</sub>")
            return

        if node.text:
            text_buf.append(node.text)

        for child in node:
            _walk(child)

        if node.tail:
            text_buf.append(node.tail)

    def _extract_inner(node: etree._Element) -> str:
        res = []
        if node.text:
            res.append(node.text)
        for child in node:
            if child.tag != "Rt":
                res.append("".join(child.itertext()))
        return "".join(res)

    _walk(element)
    cleaned = "".join(text_buf)
    cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
    return cleaned


def parse_table_struct(table_elem: etree._Element) -> TableContent:
    """Parse TableStruct element to TableContent model."""
    title = clean_text_asis(table_elem.find("./TableStructTitle"))
    has_span = False
    rows: list[TableRow] = []

    for tr in table_elem.findall(".//TableRow"):
        row_cells: list[TableCell] = []
        for td in tr.findall(".//TableColumn"):
            rspan = int(td.get("rowspan", "1"))
            cspan = int(td.get("colspan", "1"))
            if rspan > 1 or cspan > 1:
                has_span = True
            cell_text = clean_text_asis(td)
            row_cells.append(TableCell(text=cell_text, rowspan=rspan, colspan=cspan))
        if row_cells:
            rows.append(TableRow(cells=row_cells))

    return TableContent(title=title, has_span=has_span, rows=rows)


def parse_item(item_elem: etree._Element) -> ItemContent:
    """Parse Item, Subitem1~Subitem10 elements recursively."""
    title_elem = None
    title_tags = [
        "ItemTitle",
        "Subitem1Title",
        "Subitem2Title",
        "Subitem3Title",
        "Subitem4Title",
        "Subitem5Title",
    ]
    for t_name in title_tags:
        t_node = item_elem.find(f"./{t_name}")
        if t_node is not None:
            title_elem = t_node
            break

    title = clean_text_asis(title_elem)
    sentences = [
        clean_text_asis(s)
        for s in item_elem.findall("./ItemSentence/Sentence")
        + item_elem.findall("./Subitem1Sentence/Sentence")
        + item_elem.findall("./Subitem2Sentence/Sentence")
        if clean_text_asis(s)
    ]

    tables = [parse_table_struct(t) for t in item_elem.findall("./TableStruct")]

    subitems: list[ItemContent] = []
    for tag_name in [
        "Subitem1",
        "Subitem2",
        "Subitem3",
        "Subitem4",
        "Subitem5",
        "Subitem6",
        "Subitem7",
        "Subitem8",
        "Subitem9",
        "Subitem10",
    ]:
        for sub in item_elem.findall(f"./{tag_name}"):
            subitems.append(parse_item(sub))

    return ItemContent(title=title, sentences=sentences, subitems=subitems, tables=tables)


def parse_paragraph(para_elem: etree._Element) -> ParagraphContent:
    """Parse Paragraph element."""
    p_num = clean_text_asis(para_elem.find("./ParagraphNum"))
    sentences = [clean_text_asis(s) for s in para_elem.findall("./ParagraphSentence/Sentence")]
    items = [parse_item(item) for item in para_elem.findall("./Item")]
    tables = [parse_table_struct(t) for t in para_elem.findall("./TableStruct")]

    return ParagraphContent(
        num=p_num,
        sentences=[s for s in sentences if s],
        items=items,
        tables=tables,
    )


def generate_article_id(num_str: str) -> str:
    """Generate article ID from Num attribute (handles branch numbers like 2_2)."""
    if not num_str:
        return "art_unknown"
    if num_str.isdigit():
        return f"art_{int(num_str):03d}"
    return f"art_{num_str}"


def parse_article(
    art_elem: etree._Element,
    part: str = "",
    chapter: str = "",
    section: str = "",
    subsection: str = "",
    division: str = "",
) -> ArticleContent:
    """Parse Article element."""
    num_str = art_elem.get("Num", "")
    art_id = generate_article_id(num_str)
    art_title = clean_text_asis(art_elem.find("./ArticleTitle"))
    art_caption = clean_text_asis(art_elem.find("./ArticleCaption"))

    paragraphs = [parse_paragraph(p) for p in art_elem.findall("./Paragraph")]

    return ArticleContent(
        article_id=art_id,
        num=num_str,
        title=art_title,
        caption=art_caption,
        paragraphs=paragraphs,
        part=part,
        chapter=chapter,
        section=section,
        subsection=subsection,
        division=division,
    )


def parse_law_xml(xml_content: str, law_id: str = "") -> ParsedLawData:
    """Parse e-Gov Law XML content to ParsedLawData."""
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_content.encode("utf-8"), parser=parser)

    law_num_elem = root.find(".//LawNum")
    law_title_elem = root.find(".//LawTitle")

    metadata = LawMetadata(
        era=root.get("Era", ""),
        year=int(root.get("Year", "0")),
        num=int(root.get("Num", "0")),
        law_type=root.get("LawType", ""),
        law_num_text=clean_text_asis(law_num_elem),
        title=clean_text_asis(law_title_elem),
        title_kana=law_title_elem.get("Kana", "") if law_title_elem is not None else "",
        abbrev=law_title_elem.get("Abbrev", "") if law_title_elem is not None else "",
        law_id=law_id,
    )

    # 2. MainProvision Articles
    articles: list[ArticleContent] = []
    main_provision = root.find(".//MainProvision")

    if main_provision is not None:
        curr_part = ""
        curr_chapter = ""
        curr_section = ""
        curr_sub = ""
        curr_div = ""

        def _traverse(elem: etree._Element):
            nonlocal curr_part, curr_chapter, curr_section, curr_sub, curr_div
            tag = elem.tag

            if tag == "PartTitle":
                curr_part = clean_text_asis(elem)
            elif tag == "ChapterTitle":
                curr_chapter = clean_text_asis(elem)
            elif tag == "SectionTitle":
                curr_section = clean_text_asis(elem)
            elif tag == "SubsectionTitle":
                curr_sub = clean_text_asis(elem)
            elif tag == "DivisionTitle":
                curr_div = clean_text_asis(elem)
            elif tag == "Article":
                articles.append(
                    parse_article(
                        elem,
                        part=curr_part,
                        chapter=curr_chapter,
                        section=curr_section,
                        subsection=curr_sub,
                        division=curr_div,
                    )
                )
                return  # Don't recurse inside Article again

            for child in elem:
                _traverse(child)

        _traverse(main_provision)

    # 3. SupplProvisions
    suppl_provisions: list[SupplProvisionContent] = []
    for idx, suppl_elem in enumerate(root.findall(".//SupplProvision")):
        label = clean_text_asis(suppl_elem.find("./SupplProvisionLabel"))
        amend_num = suppl_elem.get("AmendLawNum", "")
        suppl_id = "suppl_main" if idx == 0 and not amend_num else f"suppl_{idx:03d}"

        s_articles = [parse_article(a) for a in suppl_elem.findall(".//Article")]
        s_paragraphs = [parse_paragraph(p) for p in suppl_elem.findall("./Paragraph")]

        suppl_provisions.append(
            SupplProvisionContent(
                suppl_id=suppl_id,
                label=label or "附　則",
                amend_law_num=amend_num,
                articles=s_articles,
                paragraphs=s_paragraphs,
            )
        )

    # 4. Appendices (AppdxTable, AppdxStyle, etc.)
    appendices: list[AppdxContent] = []
    appdx_tags = [
        ("AppdxTable", "table", "./AppdxTableTitle"),
        ("AppdxStyle", "style", "./AppdxStyleTitle"),
        ("AppdxFig", "fig", "./AppdxFigTitle"),
        ("AppdxNote", "note", "./AppdxNoteTitle"),
        ("AppdxFormat", "format", "./AppdxFormatTitle"),
    ]

    for tag, appdx_type, title_xpath in appdx_tags:
        for idx, elem in enumerate(root.findall(f".//{tag}")):
            title = clean_text_asis(elem.find(title_xpath))
            appdx_id = f"{appdx_type}_{idx + 1:03d}"
            # ASIS inner text / html extraction
            body_text = clean_text_asis(elem)
            appendices.append(
                AppdxContent(
                    appdx_id=appdx_id,
                    appdx_type=appdx_type,
                    title=title or appdx_id,
                    body=body_text,
                )
            )

    return ParsedLawData(
        metadata=metadata,
        articles=articles,
        suppl_provisions=suppl_provisions,
        appendices=appendices,
    )
