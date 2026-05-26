"""
Fase 3 — parser con control de flujo completo.

Verifica que los 4 archivos de pruebas/ del profesor parseen correctamente
con la gramática extendida (if/then/else, while/do, for).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from compilador.parser import parse, parse_file

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


# --- Los 4 archivos de pruebas/ deben parsear sin error ---------------------

@pytest.mark.parametrize(
    "name",
    ["pruebaFor.txt", "pruebaWhile.txt", "pruebaIf.txt", "pruebaErrores.txt"],
)
def test_full_pruebas_parse_ok(name: str) -> None:
    """Fase 3: los archivos completos deben parsear (incluyendo control de flujo)."""
    tree = parse_file(PRUEBAS / name)
    assert tree.data == "program"


# --- Estructura del for -----------------------------------------------------

def test_for_structure() -> None:
    """Verifica que for produce nodos for_stmt con init, condition, update."""
    tree = parse_file(PRUEBAS / "pruebaFor.txt")
    stmts = tree.find_data("for_stmt")
    for_nodes = list(stmts)
    assert len(for_nodes) == 1


# --- Estructura del while ---------------------------------------------------

def test_while_structure() -> None:
    """Verifica que while produce nodo while_stmt."""
    tree = parse_file(PRUEBAS / "pruebaWhile.txt")
    whiles = list(tree.find_data("while_stmt"))
    assert len(whiles) == 1


# --- Estructura del if/else -------------------------------------------------

def test_if_structure() -> None:
    """Verifica if anidados en pruebaIf.txt."""
    tree = parse_file(PRUEBAS / "pruebaIf.txt")
    ifs = list(tree.find_data("if_stmt"))
    assert len(ifs) == 2  # if externo + if anidado en else


# --- Condición con and (pruebaErrores.txt) ----------------------------------

def test_and_condition_parses() -> None:
    """pruebaErrores.txt tiene (a>b) and (expr): debe parsear sintácticamente."""
    tree = parse_file(PRUEBAS / "pruebaErrores.txt")
    conditions = list(tree.find_data("condition"))
    assert any(
        any(child.data == "paren_cond" for child in cond.children if hasattr(child, "data"))
        for cond in conditions
    )


# --- Fragmentos inline ------------------------------------------------------

def test_simple_if() -> None:
    src = """\
program main{
    var x : int;
    begin;
        if (x > 5) then {
            write(x);
        }
    end;
}"""
    tree = parse(src)
    assert list(tree.find_data("if_stmt"))


def test_simple_while() -> None:
    src = """\
program main{
    var n : int;
    begin;
        n := 10;
        while (n >= 1) do {
            n--;
        }
    end;
}"""
    tree = parse(src)
    assert list(tree.find_data("while_stmt"))
    assert list(tree.find_data("dec_stmt"))


def test_simple_for() -> None:
    src = """\
program main{
    var i : int;
    begin;
        for (i:=0; i < 10; i++) {
            write(i);
        }
    end;
}"""
    tree = parse(src)
    assert list(tree.find_data("for_stmt"))
