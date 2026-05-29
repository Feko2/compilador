"""Analizador léxico (Fase 1): solo emite tokens; no construye AST."""

from __future__ import annotations

from pathlib import Path

from lark import Token

from compilador.lark_util import open_lark

_TOKENS_LARK = Path(__file__).with_name("tokens.lark")


def _lark():
    return open_lark(_TOKENS_LARK)


def tokenize(text: str) -> tuple[Token, ...]:
    """Devuelve la secuencia de tokens (sin tokens ignorados como espacios)."""
    return tuple(_lark().lex(text))


def tokenize_file(path: Path) -> tuple[Token, ...]:
    return tokenize(path.read_text(encoding="utf-8"))
