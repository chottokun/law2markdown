"""Data models for law2markdown."""

from dataclasses import dataclass, field


@dataclass
class LawMetadata:
    """法令メタデータ."""

    era: str = ""
    year: int = 0
    num: int = 0
    law_type: str = ""
    law_num_text: str = ""
    title: str = ""
    title_kana: str = ""
    abbrev: str = ""
    law_id: str = ""
    promulgate_date: str = ""


@dataclass
class TableCell:
    """表セル."""

    text: str
    rowspan: int = 1
    colspan: int = 1


@dataclass
class TableRow:
    """表行."""

    cells: list[TableCell] = field(default_factory=list)


@dataclass
class TableContent:
    """表構造."""

    title: str = ""
    has_span: bool = False
    rows: list[TableRow] = field(default_factory=list)


@dataclass
class ItemContent:
    """号コンテンツ（再帰構造）."""

    title: str = ""
    sentences: list[str] = field(default_factory=list)
    subitems: list["ItemContent"] = field(default_factory=list)
    tables: list[TableContent] = field(default_factory=list)


@dataclass
class ParagraphContent:
    """項コンテンツ."""

    num: str = ""
    sentences: list[str] = field(default_factory=list)
    items: list[ItemContent] = field(default_factory=list)
    tables: list[TableContent] = field(default_factory=list)


@dataclass
class ArticleContent:
    """条文コンテンツ."""

    article_id: str = ""
    num: str = ""
    title: str = ""
    caption: str = ""
    paragraphs: list[ParagraphContent] = field(default_factory=list)
    part: str = ""
    chapter: str = ""
    section: str = ""
    subsection: str = ""
    division: str = ""


@dataclass
class SupplProvisionContent:
    """附則コンテンツ."""

    suppl_id: str = ""
    label: str = ""
    amend_law_num: str = ""
    articles: list[ArticleContent] = field(default_factory=list)
    paragraphs: list[ParagraphContent] = field(default_factory=list)


@dataclass
class AppdxContent:
    """別表・別記様式コンテンツ."""

    appdx_id: str = ""
    appdx_type: str = ""  # "table", "style", "fig", "note", "format"
    title: str = ""
    body: str = ""
