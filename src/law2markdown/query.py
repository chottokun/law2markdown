"""Query engine for exploring structured legal knowledge base (Agentic Legal RAG)."""

import re
from pathlib import Path
from typing import Any


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and markdown body from content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_raw = parts[1]
    body = parts[2].lstrip("\r\n")

    # Simple YAML key-value parser to avoid extra external dependencies
    fm: dict[str, Any] = {}
    curr_key = ""
    curr_list: list[str] = []

    for line in fm_raw.splitlines():
        if not line.strip():
            continue

        # If indented, handle list of scalar values for current key
        if line.startswith("  ") or line.startswith("\t"):
            line_stripped = line.strip()
            if line_stripped.startswith("- ") and curr_key:
                val = line_stripped[2:].strip().strip("\"'")
                # If scalar value (not key-value like - id: ...)
                if ":" not in val:
                    curr_list.append(val)
                    fm[curr_key] = curr_list
            continue

        # Top-level key
        if ":" in line:
            curr_key = ""
            curr_list = []
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            if v == "true":
                fm[k] = True
            elif v == "false":
                fm[k] = False
            elif v.isdigit():
                fm[k] = int(v)
            elif v == "[]":
                fm[k] = []
            elif not v:
                curr_key = k
                curr_list = []
                fm[k] = curr_list
            else:
                fm[k] = v

    return fm, body


def _find_law_dir(kb_dir: str | Path, law_title_or_id: str) -> Path | None:
    """Find the law directory within kb_dir by title or law_id."""
    kb_path = Path(kb_dir)
    if not kb_path.exists():
        return None

    # Check direct match by directory name
    direct = kb_path / law_title_or_id
    if direct.is_dir():
        return direct

    # Search directories with matching title or index.md frontmatter
    for d in kb_path.iterdir():
        if not d.is_dir():
            continue
        if d.name.startswith(law_title_or_id):
            return d
        index_file = d / "index.md"
        if index_file.exists():
            fm, _ = _parse_frontmatter(index_file.read_text(encoding="utf-8"))
            if fm.get("law_id") == law_title_or_id or fm.get("title") == law_title_or_id:
                return d

    return None


def get_article(
    kb_dir: str | Path,
    law_title_or_id: str,
    article_num: str | int,
    paragraph_num: int | None = None,
) -> dict[str, Any]:
    """Retrieve full article or specific paragraph slice with metadata."""
    law_dir = _find_law_dir(kb_dir, law_title_or_id)
    if not law_dir:
        return {"found": False, "error": f"Law not found: {law_title_or_id}"}

    articles_dir = law_dir / "articles"
    if not articles_dir.exists():
        return {"found": False, "error": f"Articles directory not found for: {law_title_or_id}"}

    target_num_str = str(article_num)
    formatted_num = f"{int(target_num_str):03d}" if target_num_str.isdigit() else target_num_str

    matched_file: Path | None = None
    for md_file in sorted(articles_dir.glob("*.md")):
        if md_file.name == "index.md":
            continue
        if md_file.name.startswith(f"art_{formatted_num}_") or md_file.name.startswith(
            f"art_{target_num_str}_"
        ):
            matched_file = md_file
            break

    if not matched_file:
        return {"found": False, "error": f"Article {article_num} not found in {law_dir.name}"}

    content = matched_file.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(content)

    # Slice specific paragraph if requested
    if paragraph_num is not None:
        p_anchor = f'<a id="p{paragraph_num}"></a>'
        next_p_anchor = f'<a id="p{paragraph_num + 1}"></a>'

        start_pos = body.find(p_anchor)
        if start_pos == -1:
            return {
                "found": False,
                "error": f"Paragraph {paragraph_num} not found in article {article_num}",
            }

        end_pos = body.find(next_p_anchor, start_pos)
        if end_pos == -1:
            # Check reference section divider
            ref_pos = body.find("\n---", start_pos)
            end_pos = ref_pos if ref_pos != -1 else len(body)

        sliced_body = body[start_pos:end_pos].strip()
        return {
            "found": True,
            "law": law_dir.name,
            "article_id": matched_file.stem,
            "article_num": target_num_str,
            "paragraph_num": paragraph_num,
            "title": fm.get("title", ""),
            "hierarchy_path": fm.get("hierarchy_path", ""),
            "body": sliced_body,
            "frontmatter": fm,
        }

    return {
        "found": True,
        "law": law_dir.name,
        "article_id": matched_file.stem,
        "article_num": target_num_str,
        "title": fm.get("title", ""),
        "hierarchy_path": fm.get("hierarchy_path", ""),
        "body": body,
        "frontmatter": fm,
    }


def get_hierarchy(
    kb_dir: str | Path,
    law_title_or_id: str,
    article_num: str | int,
) -> dict[str, Any]:
    """Retrieve article's position in legal hierarchy and sibling articles in the same chapter."""
    art_res = get_article(kb_dir, law_title_or_id, article_num)
    if not art_res["found"]:
        return art_res

    fm = art_res["frontmatter"]
    law_dir = _find_law_dir(kb_dir, law_title_or_id)
    articles_dir = law_dir / "articles"  # type: ignore

    chapter = fm.get("chapter", "")
    part = fm.get("part", "")
    siblings: list[dict[str, str]] = []

    for md_file in sorted(articles_dir.glob("*.md")):
        if md_file.name == "index.md":
            continue
        s_fm, _ = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
        # Match chapter if exists, otherwise part
        if chapter and s_fm.get("chapter") == chapter:
            siblings.append({"article_id": md_file.stem, "title": s_fm.get("title", md_file.stem)})
        elif not chapter and part and s_fm.get("part") == part:
            siblings.append({"article_id": md_file.stem, "title": s_fm.get("title", md_file.stem)})
        elif not chapter and not part:
            siblings.append({"article_id": md_file.stem, "title": s_fm.get("title", md_file.stem)})

    return {
        "found": True,
        "law": law_dir.name,  # type: ignore
        "article_id": art_res["article_id"],
        "hierarchy_path": fm.get("hierarchy_path", ""),
        "part": part,
        "chapter": chapter,
        "section": fm.get("section", ""),
        "sibling_articles": siblings,
    }


def trace_references(
    kb_dir: str | Path,
    law_title_or_id: str,
    article_num: str | int,
    direction: str = "both",
) -> dict[str, Any]:
    """Traverse outbound citations and inbound reverse citations."""
    art_res = get_article(kb_dir, law_title_or_id, article_num)
    if not art_res["found"]:
        return art_res

    fm = art_res["frontmatter"]
    law_dir = _find_law_dir(kb_dir, law_title_or_id)
    articles_dir = law_dir / "articles"  # type: ignore

    outbound_ids = fm.get("outbound_references", [])
    inbound_ids = fm.get("inbound_references", [])

    def _resolve_refs(ref_list: list[str]) -> list[dict[str, str]]:
        resolved = []
        for ref_id in ref_list:
            target_file = articles_dir / f"{ref_id}.md"
            if target_file.exists():
                t_fm, _ = _parse_frontmatter(target_file.read_text(encoding="utf-8"))
                resolved.append({"article_id": ref_id, "title": t_fm.get("title", ref_id)})
            else:
                resolved.append({"article_id": ref_id, "title": ref_id})
        return resolved

    result: dict[str, Any] = {
        "found": True,
        "law": law_dir.name,  # type: ignore
        "article_id": art_res["article_id"],
        "title": fm.get("title", ""),
    }

    if direction in ("outbound", "both"):
        result["outbound_references"] = _resolve_refs(outbound_ids)
    if direction in ("inbound", "both"):
        result["inbound_references"] = _resolve_refs(inbound_ids)

    return result


def lookup_term(
    kb_dir: str | Path,
    law_title_or_id: str,
    term: str,
) -> dict[str, Any]:
    """Lookup statutory term definition from definitions.md."""
    law_dir = _find_law_dir(kb_dir, law_title_or_id)
    if not law_dir:
        return {"found": False, "error": f"Law not found: {law_title_or_id}"}

    def_file = law_dir / "definitions.md"
    if not def_file.exists():
        return {
            "found": False,
            "error": f"No definitions registry found for: {law_dir.name}",
        }

    content = def_file.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(content)

    # Search for term anchor in definitions.md
    term_pattern = re.compile(
        rf"## (?:<a id=\"{re.escape(term)}\"></a>)?{re.escape(term)}\n+(.*?)(?=\n## |\n---|\Z)",
        re.DOTALL,
    )
    match = term_pattern.search(body)
    if not match:
        return {"found": False, "error": f"Term '{term}' not found in {law_dir.name}"}

    section_text = match.group(1).strip()
    defn_match = re.search(r"- \*\*定義文\*\*: (.*)", section_text)
    defn_text = defn_match.group(1).strip() if defn_match else section_text

    art_match = re.search(r"- \*\*定義条文\*\*: \[(.*?)\]\((.*?)\)", section_text)
    def_art = art_match.group(1).strip() if art_match else ""

    return {
        "found": True,
        "law": law_dir.name,
        "term": term,
        "definition": defn_text,
        "article": def_art,
        "raw_section": section_text,
    }
