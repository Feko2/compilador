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
    decls = tree.children[3]
    assert decls.data == "decls"
    idents = [c.value for c in decls.children[1].children if c.type == "IDENT"]
    assert idents == ["i", "n", "x"]


@pytest.mark.parametrize(
    "name",
    ["pruebaFor.txt", "pruebaWhile.txt", "pruebaIf.txt", "pruebaErrores.txt"],
)
def test_full_pruebas_reject_without_control_flow_grammar(name: str) -> None:
    with pytest.raises(UnexpectedInput):
        parse_file(PRUEBAS / name)


def test_invalid_syntax() -> None:
    with pytest.raises(UnexpectedInput):
        parse("program main { var x : int; begin; x := ; end; }")
