"""Extra — arreglos y funciones."""

from __future__ import annotations

from pathlib import Path

from compilador.ast_builder import build_ast_from_file
from compilador.interpreter import run
from compilador.semantic import analyze

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


def test_prueba_array_runs() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaArray.txt")
    _, errors = analyze(ast)
    assert errors == []
    result = run(ast)
    assert result.output == ["prueba arreglo", "60"]


def test_prueba_funcion_runs() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaFuncion.txt")
    _, errors = analyze(ast)
    assert errors == []
    result = run(ast)
    assert result.output == ["prueba funcion", "7", "25", "14"]


def test_array_out_of_bounds_runtime() -> None:
    from compilador.ast_builder import build_ast
    from compilador.interpreter import run as execute

    src = """\
program main{
    var a : array [2] of int;
    begin;
        a[5] := 1;
    end;
}"""
    ast = build_ast(src)
    _, errors = analyze(ast)
    assert errors == []
    result = execute(ast)
    assert not result.ok
    assert result.errors[0].phase == "runtime"


def test_undefined_function_semantic() -> None:
    from compilador.ast_builder import build_ast

    src = """\
program main{
    var x : int;
    begin;
        x := noexiste(1);
    end;
}"""
    ast = build_ast(src)
    _, errors = analyze(ast)
    assert any("no definida" in e.message for e in errors)
