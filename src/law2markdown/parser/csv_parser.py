"""CSV parser for e-Gov law list CSV (e.g. 20.csv)."""

import csv
import io
from typing import Any


def parse_law_csv_content(csv_text: str) -> dict[str, dict[str, Any]]:
    """Parse e-Gov CSV content and return mapping.

    Keyed by law directory ID (e.g. 321AC.../URL path).
    """
    result: dict[str, dict[str, Any]] = {}

    # Strip UTF-8 BOM if present
    if csv_text.startswith("\ufeff"):
        csv_text = csv_text[1:]

    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        url = row.get("本文URL", "").strip()
        law_id = row.get("法令ID", "").strip()

        # Extract directory key from URL (e.g. https://laws.e-gov.go.jp/law/321AC.../20160401_426AC...)
        key = ""
        if url:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                key = f"{parts[-2]}_{parts[-1]}"

        if not key:
            key = law_id

        if not key:
            continue

        result[key] = {
            "law_type": row.get("法令種別", "").strip(),
            "law_num": row.get("法令番号", "").strip(),
            "title": row.get("法令名", "").strip(),
            "title_kana": row.get("法令名読み", "").strip(),
            "old_title": row.get("旧法令名", "").strip(),
            "promulgate_date": row.get("公布日", "").strip(),
            "amend_law_title": row.get("改正法令名", "").strip(),
            "amend_law_num": row.get("改正法令番号", "").strip(),
            "amend_promulgate_date": row.get("改正法令公布日", "").strip(),
            "enforce_date": row.get("施行日", "").strip(),
            "enforce_note": row.get("施行日備考", "").strip(),
            "law_id": law_id,
            "url": url,
            "is_unexecuted": row.get("未施行", "").strip() == "○",
        }

    return result
