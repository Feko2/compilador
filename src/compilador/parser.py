"""
Analizador sintáctico (Fases 2–3 + extra).

Fase 2: programa núcleo (var, begin/end, write, :=, expresiones).
Fase 3: control de flujo (if/then/else, while/do, for).
Extra:  arreglos (array [N] of int, arr[i]) y funciones (function ...).
"""

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
    """Lee un archivo fuente y devuelve su árbol de parseo."""
    return parse(path.read_text(encoding="utf-8"))
