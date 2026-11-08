"""Reference analyzer for extracting citations, delegations, and building graphs."""

import re

from law2markdown.models import AppdxContent, ArticleContent, ItemContent

KANJI_DIGITS = {
    "〇": 0,
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

KANJI_UNITS = {
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
}


def kanji_to_int(k_str: str) -> int:
    """Convert Japanese kanji numeral string to integer."""
    if not k_str:
        return 0
    if k_str.isdigit():
        return int(k_str)

    # Direct position digits like 二〇一五
    if all(ch in KANJI_DIGITS for ch in k_str):
        val = 0
        for ch in k_str:
            val = val * 10 + KANJI_DIGITS[ch]
        return val

    total = 0
    section_val = 0
    curr_digit = 1
    digit_set = False

    for ch in k_str:
        if ch in KANJI_DIGITS:
            curr_digit = KANJI_DIGITS[ch]
            digit_set = True
        elif ch in KANJI_UNITS:
            unit = KANJI_UNITS[ch]
            if unit == 10000:
                if not digit_set and curr_digit == 1:
                    section_val += 1
                else:
                    section_val += curr_digit
                total += section_val * 10000
                section_val = 0
                curr_digit = 1
                digit_set = False
            else:
                if not digit_set:
                    curr_digit = 1
                section_val += curr_digit * unit
                curr_digit = 0
                digit_set = False
        else:
            continue

    if digit_set:
        section_val += curr_digit
    total += section_val
    return total


def extract_references_from_text(text: str) -> dict[str, list[str]]:
    """Extract citations, relative references, and delegations from text."""
    results: dict[str, list[str]] = {
        "articles": [],
        "relative": [],
        "delegations": [],
        "tables": [],
    }

    # Relative references
    rel_patterns = ["前条", "次条", "前二条", "同条"]
    for rel in rel_patterns:
        if rel in text:
            results["relative"].append(rel)

    # Article citations (e.g. 第十二条, 第12条, 第一条の二)
    art_matches = re.findall(
        r"第([〇一二三四五六七八九十百千万\d]+)条(?:の([〇一二三四五六七八九十百千万\d]+))?",
        text,
    )
    for main_num, sub_num in art_matches:
        raw_match = f"第{main_num}条" + (f"の{sub_num}" if sub_num else "")
        results["articles"].append(raw_match)

    # Delegation patterns (e.g. 政令で定める, 厚生労働省令で定める)
    del_matches = re.findall(
        r"([^\s、。]{0,10}(?:政令|府省令|省令|規則|告示|府令|令)で定め(?:る|た|ている))",
        text,
    )
    results["delegations"].extend(del_matches)

    # Appendix tables (e.g. 別表第一, 別表第1)
    tbl_matches = re.findall(r"別表第?([〇一二三四五六七八九十百千万\d]+)", text)
    for m in tbl_matches:
        results["tables"].append(f"別表第{m}")

    return results


def _collect_article_text(art: ArticleContent) -> str:
    """Collect all sentences from an article's paragraphs and items."""
    parts = []

    def _walk_item(item: ItemContent):
        parts.extend(item.sentences)
        for sub in item.subitems:
            _walk_item(sub)

    for p in art.paragraphs:
        parts.extend(p.sentences)
        for item in p.items:
            _walk_item(item)

    return " ".join(parts)


def build_reference_graph(
    articles: list[ArticleContent],
    appendices: list[AppdxContent] | None = None,
) -> None:
    """Analyze citations in articles and populate outbound and inbound references."""
    # Build maps for fast resolution
    # Map from canonical article num string to ArticleContent
    art_by_num: dict[str, ArticleContent] = {}
    art_by_title: dict[str, ArticleContent] = {}
    table_by_title: dict[str, AppdxContent] = {}

    for art in articles:
        if art.num:
            art_by_num[art.num] = art
        if art.title:
            art_by_title[art.title] = art

    if appendices:
        for app in appendices:
            if app.appdx_type == "table":
                table_by_title[app.title] = app

    # Collect outbound references for each article
    for idx, art in enumerate(articles):
        out_refs: set[str] = set()
        text = _collect_article_text(art)
        extracted = extract_references_from_text(text)

        # 1. Resolve relative references
        for rel in extracted["relative"]:
            if rel == "前条" and idx > 0:
                out_refs.add(articles[idx - 1].article_id)
            elif rel == "次条" and idx + 1 < len(articles):
                out_refs.add(articles[idx + 1].article_id)
            elif rel == "前二条":
                if idx > 0:
                    out_refs.add(articles[idx - 1].article_id)
                if idx > 1:
                    out_refs.add(articles[idx - 2].article_id)

        # 2. Resolve article citations
        for cite in extracted["articles"]:
            # Check title match (e.g. 第一条, 第二条の二)
            if cite in art_by_title:
                target_art = art_by_title[cite]
                if target_art.article_id != art.article_id:
                    out_refs.add(target_art.article_id)
                continue

            # Parse number
            m = re.match(
                r"第([〇一二三四五六七八九十百千万\d]+)条(?:の([〇一二三四五六七八九十百千万\d]+))?",
                cite,
            )
            if m:
                main_val = str(kanji_to_int(m.group(1)))
                sub_val = str(kanji_to_int(m.group(2))) if m.group(2) else ""
                target_num = f"{main_val}_{sub_val}" if sub_val else main_val

                if target_num in art_by_num:
                    target_art = art_by_num[target_num]
                    if target_art.article_id != art.article_id:
                        out_refs.add(target_art.article_id)

        # 3. Resolve table citations
        for tbl in extracted["tables"]:
            for t_title, t_app in table_by_title.items():
                if tbl in t_title or t_title in tbl:
                    out_refs.add(t_app.appdx_id)

        art.outbound_references = sorted(out_refs)

    # Build inbound references (reverse index)
    inbound_map: dict[str, set[str]] = {a.article_id: set() for a in articles}
    for art in articles:
        for out_id in art.outbound_references:
            if out_id in inbound_map:
                inbound_map[out_id].add(art.article_id)

    for art in articles:
        art.inbound_references = sorted(inbound_map.get(art.article_id, set()))
