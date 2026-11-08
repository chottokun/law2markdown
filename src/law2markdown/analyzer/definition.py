"""Legal definition analyzer for extracting statutory term definitions."""

import re
from dataclasses import dataclass

from law2markdown.analyzer.reference import _collect_article_text
from law2markdown.models import ArticleContent


@dataclass
class TermDefinition:
    """法定用語の定義情報."""

    term: str
    definition_text: str
    article_id: str = ""
    article_title: str = ""
    scope: str = "本法"


def extract_definitions_from_text(text: str) -> list[TermDefinition]:
    """Extract statutory term definitions from text using legal drafting patterns."""
    definitions: list[TermDefinition] = []

    # Pattern 1: 「用語」とは、...をいう。
    pattern_explicit = re.compile(r"「([^「」]{1,50})」とは、([^。]{2,500}をいう(?:ものとする)?)")
    for m in pattern_explicit.finditer(text):
        term = m.group(1).strip()
        defn = m.group(2).strip() + "。"
        definitions.append(
            TermDefinition(
                term=term,
                definition_text=defn,
                scope="本法",
            )
        )

    # Pattern 2: （以下「用語」という。） or （この章において「用語」という。）
    pattern_alias = re.compile(
        r"（([^\s（）]*?(?:以下|この章において|次条において|本節において))「([^「」]{1,50})」という。[）\)]"
    )
    for m in pattern_alias.finditer(text):
        scope_str = m.group(1).strip() or "以下"
        term = m.group(2).strip()
        definitions.append(
            TermDefinition(
                term=term,
                definition_text=f"{scope_str}「{term}」と略称または限定定義。",
                scope=scope_str,
            )
        )

    return definitions


def build_definition_registry(articles: list[ArticleContent]) -> list[TermDefinition]:
    """Build registry of defined terms across all articles and cross-reference usages."""
    registry: list[TermDefinition] = []
    term_set: set[str] = set()

    # 1. Extract definitions from all articles
    for art in articles:
        text = _collect_article_text(art)
        extracted = extract_definitions_from_text(text)
        art_defined: list[str] = []

        for d in extracted:
            d.article_id = art.article_id
            d.article_title = art.title
            if d.term not in term_set:
                term_set.add(d.term)
                registry.append(d)
            if d.term not in art_defined:
                art_defined.append(d.term)

        art.defined_terms = sorted(art_defined)

    # 2. Detect usages in other articles
    for art in articles:
        text = _collect_article_text(art)
        ref_terms: set[str] = set()

        for d in registry:
            # If term is defined in this article, skip referencing itself
            if d.term in art.defined_terms:
                continue
            # Must appear in text and length >= 2
            if len(d.term) >= 2 and d.term in text:
                ref_terms.add(d.term)

        art.referenced_terms = sorted(ref_terms)

    return registry
