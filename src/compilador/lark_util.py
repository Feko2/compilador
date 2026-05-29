"""Carga de gramáticas Lark con terminales compartidos (`lexer/terminals.lark`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lark import Lark

_TERMINALS = Path(__file__).parent / "lexer" / "terminals.lark"


def compose_lark(main: Path) -> str:
    """Concatena terminales + reglas del archivo principal."""
    return _TERMINALS.read_text(encoding="utf-8") + "\n" + main.read_text(encoding="utf-8")


@lru_cache(maxsize=8)
def open_lark(main: Path, *, start: str | None = None) -> Lark:
    text = compose_lark(main)
    kwargs: dict = {"parser": "lalr", "lexer": "basic", "source_path": str(main)}
    if start is not None:
        kwargs["start"] = start
    return Lark(text, **kwargs)
