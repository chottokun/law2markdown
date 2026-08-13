"""Table renderer for GFM pipe table and HTML table."""

from law2markdown.models import TableContent


def render_table(table: TableContent) -> str:
    """Render TableContent to GFM pipe table or HTML table.

    If table contains rowspan or colspan > 1, render as HTML table (ASIS principle).
    Otherwise, render as standard GFM pipe table.
    """
    if not table.rows:
        return ""

    if table.has_span:
        lines = ["<table>"]
        for row in table.rows:
            lines.append("  <tr>")
            for cell in row.cells:
                attrs = []
                if cell.rowspan > 1:
                    attrs.append(f'rowspan="{cell.rowspan}"')
                if cell.colspan > 1:
                    attrs.append(f'colspan="{cell.colspan}"')
                attr_str = f" {' '.join(attrs)}" if attrs else ""
                lines.append(f"    <td{attr_str}>{cell.text}</td>")
            lines.append("  </tr>")
        lines.append("</table>")
        return "\n".join(lines)
    else:
        rows_data: list[list[str]] = []
        for row in table.rows:
            cols = [cell.text.replace("|", "\\|") for cell in row.cells]
            rows_data.append(cols)

        if not rows_data:
            return ""

        max_cols = max(len(r) for r in rows_data)
        md_lines = []

        header = rows_data[0] + [""] * (max_cols - len(rows_data[0]))
        md_lines.append("| " + " | ".join(header) + " |")
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        for r in rows_data[1:]:
            padded = r + [""] * (max_cols - len(r))
            md_lines.append("| " + " | ".join(padded) + " |")

        return "\n".join(md_lines)
