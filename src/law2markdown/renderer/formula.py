"""Formula renderer converting e-Gov XML ArithFormula text to LaTeX."""

import re


def render_formula(formula_text: str) -> str:
    """Convert raw formula text to LaTeX formatted string."""
    tex_formula = formula_text.replace("÷", r"\div").replace("×", r"\times")
    tex_formula = re.sub(r"（([^）]+)／([^）]+)）", r"\\frac{\1}{\2}", tex_formula)
    tex_formula = re.sub(r"\s+", " ", tex_formula).strip()
    return f"$ {tex_formula} $"
