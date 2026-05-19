"""Analizador sintáctico núcleo (Fase 2): sin control de flujo."""

from __future__ import annotations

from pathlib import Path

from lark import Tree

from compilador.lark_util import open_lark

_PROGRAM_LARK = Path(__file__).parent / "grammar" / "program.lark"


def _lark():
    return open_lark(_PROGRAM_LARK, start="program")


def parse(text: str) -> Tree:
    """Parsea un programa completo (regla `program`)."""
    return _lark().parse(text)


def parse_file(path: Path) -> Tree:
    return parse(path.read_text(encoding="utf-8"))
