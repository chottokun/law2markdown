"""Tests for table renderer."""

from law2markdown.models import TableCell, TableContent, TableRow
from law2markdown.renderer.table import render_table


def test_render_simple_table():
    table = TableContent(
        title="別表第一",
        has_span=False,
        rows=[
            TableRow(cells=[TableCell(text="項目"), TableCell(text="基準")]),
            TableRow(cells=[TableCell(text="イ"), TableCell(text="100分率")]),
            TableRow(cells=[TableCell(text="ロ"), TableCell(text="200分率")]),
        ],
    )
    rendered = render_table(table)
    expected = "| 項目 | 基準 |\n| --- | --- |\n| イ | 100分率 |\n| ロ | 200分率 |"
    assert rendered == expected


def test_render_complex_table_with_spans():
    table = TableContent(
        title="",
        has_span=True,
        rows=[
            TableRow(cells=[TableCell(text="区分", rowspan=2), TableCell(text="内容", colspan=2)]),
            TableRow(cells=[TableCell(text="A"), TableCell(text="B")]),
        ],
    )
    rendered = render_table(table)
    assert "<table>" in rendered
    assert '<td rowspan="2">区分</td>' in rendered
    assert '<td colspan="2">内容</td>' in rendered
    assert "</table>" in rendered
