"""Fase 2 — parser núcleo sobre fragmentos de `pruebas/` (sin if/while/for)."""

from __future__ import annotations

from pathlib import Path

import pytest
from lark import UnexpectedInput

from compilador.parser import parse, parse_file

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"

# Fragmento de pruebaFor.txt sin el `for`.
NUCLEO_FOR = """\
program main{
\tvar i,n,x : int;
\tbegin;
\t\twrite("factorial for");
\t\tx:=1;
\t\tn:=5;
\t\twrite(x);
\tend;
}"""

# Fragmento de pruebaWhile.txt sin el `while`.
NUCLEO_WHILE = """\
program main{
\tvar i,n,x : int;
\tbegin;
\t\twrite("factorial while");
\t\tn := 5;
\t\tx := 1;
\t\twrite(x);
\tend;
}"""

# Fragmento de pruebaIf.txt sin `if` (solo declaraciones, write y asignaciones).
NUCLEO_IF = """\
program main{
\tvar a,b,x,y,i : int;
\tbegin;
\t\twrite("prueba if");
\t\ta := 5;
\t\tb :=  a + 3;
\t\tx := b +5;
\t\ty := x + a;
\t\twrite(i);
\tend;
}"""


@pytest.mark.parametrize("source", [NUCLEO_FOR, NUCLEO_WHILE, NUCLEO_IF])
def test_nucleo_fragments_parse(source: str) -> None:
    tree = parse(source)
    assert tree.data == "program"


def test_nucleo_for_structure() -> None:
    tree = parse(NUCLEO_FOR)
    assert tree.children[0].type == "PROGRAM"
    top_level = tree.children[3]
    assert top_level.data == "top_level_items"
    decls = top_level.children[0].children[0]
    assert decls.data == "decls"
    declarator_list = decls.children[1].children[0]
    assert declarator_list.data == "declarator_list"
    idents = [
        d.children[0].value
        for d in declarator_list.children
        if hasattr(d, "data")  # nodos declarador (omite tokens COMMA)
    ]
    assert idents == ["i", "n", "x"]


def test_invalid_syntax() -> None:
    with pytest.raises(UnexpectedInput):
        parse("program main { var x : int; begin; x := ; end; }")
