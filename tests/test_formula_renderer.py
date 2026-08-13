"""Tests for formula renderer."""

from law2markdown.renderer.formula import render_formula


def test_render_simple_formula():
    raw_formula = "A ÷ B × C"
    rendered = render_formula(raw_formula)
    assert rendered == r"$ A \div B \times C $"


def test_render_fraction_formula():
    raw_formula = "（イ／ロ）"
    rendered = render_formula(raw_formula)
    assert rendered == r"$ \frac{イ}{ロ} $"
