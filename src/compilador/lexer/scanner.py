"""Analizador léxico (Fase 1): solo emite tokens; no construye AST."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lark import Lark, Token

_GRAMMAR = (Path(__file__).with_name("tokens.lark")).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _lark() -> Lark:
    return Lark(_GRAMMAR, parser="lalr", lexer="basic")


def tokenize(text: str) -> tuple[Token, ...]:
    """Devuelve la secuencia de tokens (sin tokens ignorados como espacios)."""
    return tuple(_lark().lex(text))


def tokenize_file(path: Path) -> tuple[Token, ...]:
    return tokenize(path.read_text(encoding="utf-8"))
