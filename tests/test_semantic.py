"""Fase 5 — Tests del análisis semántico."""

from __future__ import annotations

from pathlib import Path

from compilador.ast_builder import build_ast, build_ast_from_file
from compilador.semantic import analyze

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


def test_prueba_for_no_errors() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaFor.txt")
    _, errors = analyze(ast)
    assert errors == []


def test_prueba_while_no_errors() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaWhile.txt")
    _, errors = analyze(ast)
    assert errors == []


def test_prueba_if_no_errors() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaIf.txt")
    _, errors = analyze(ast)
    assert errors == []


def test_prueba_errores_detects_type_error() -> None:
    """pruebaErrores.txt tiene (a>b) and (expr_int): debe detectar error semántico."""
    ast = build_ast_from_file(PRUEBAS / "pruebaErrores.txt")
    _, errors = analyze(ast)
    assert len(errors) >= 1
    messages = " ".join(e.message for e in errors)
    assert "booleano" in messages or "condición" in messages


def test_undeclared_variable() -> None:
    src = """\
program main{
    var x : int;
    begin;
        y := 5;
    end;
}"""
    ast = build_ast(src)
    _, errors = analyze(ast)
    assert any("no declarada" in e.message for e in errors)


def test_symbol_table_populated() -> None:
    src = """\
program main{
    var a,b,c : int;
    begin;
        a := 1;
    end;
}"""
    ast = build_ast(src)
    table, errors = analyze(ast)
    assert errors == []
    assert table.is_declared("a")
    assert table.is_declared("b")
    assert table.is_declared("c")
    assert not table.is_declared("z")
