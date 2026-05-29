"""Fase 4 — Tests del AST builder."""

from __future__ import annotations

from pathlib import Path

from compilador.ast_builder import build_ast, build_ast_from_file
from compilador.ast_nodes import (
    Assign, BinOp, Comparison, For, If, Inc, IntLit, Program, Var, While, Write,
)

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


def test_simple_program_structure() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 5;
        write(x);
    end;
}"""
    ast = build_ast(src)
    assert isinstance(ast, Program)
    assert len(ast.declarations) == 1
    assert ast.declarations[0].name == "x"
    assert len(ast.body) == 2
    assert isinstance(ast.body[0], Assign)
    assert isinstance(ast.body[1], Write)


def test_assign_expr() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 2 + 3 * 4;
    end;
}"""
    ast = build_ast(src)
    assign = ast.body[0]
    assert isinstance(assign, Assign)
    assert assign.target == "x"
    # 2 + (3 * 4) por precedencia
    assert isinstance(assign.value, BinOp)
    assert assign.value.op == "+"


def test_prueba_for_ast() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaFor.txt")
    assert len(ast.declarations) == 3
    for_stmt = [s for s in ast.body if isinstance(s, For)]
    assert len(for_stmt) == 1
    assert isinstance(for_stmt[0].init, Assign)
    assert isinstance(for_stmt[0].update, Inc)


def test_prueba_while_ast() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaWhile.txt")
    whiles = [s for s in ast.body if isinstance(s, While)]
    assert len(whiles) == 1
    assert isinstance(whiles[0].condition, Comparison)
    assert whiles[0].condition.op == ">="


def test_prueba_if_ast() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaIf.txt")
    ifs = [s for s in ast.body if isinstance(s, If)]
    assert len(ifs) == 1
    # El else contiene otro if
    assert len(ifs[0].else_body) == 1
    assert isinstance(ifs[0].else_body[0], If)
