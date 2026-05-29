"""Fases 6-7 — Tests del intérprete (ejecución)."""

from __future__ import annotations

from pathlib import Path

from compilador.ast_builder import build_ast, build_ast_from_file
from compilador.interpreter import run

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


def test_prueba_for_output() -> None:
    """pruebaFor.txt calcula factorial de 4 (i:=1 a i<5) → 1*1*2*3*4 = 24."""
    ast = build_ast_from_file(PRUEBAS / "pruebaFor.txt")
    result = run(ast)
    assert result.ok
    assert result.output == ["factorial for", "24"]


def test_prueba_while_output() -> None:
    """pruebaWhile.txt calcula factorial de 5 → 120."""
    ast = build_ast_from_file(PRUEBAS / "pruebaWhile.txt")
    result = run(ast)
    assert result.ok
    assert result.output == ["factorial while", "120"]


def test_prueba_if_output() -> None:
    """pruebaIf.txt: a=5, b=8, x=13, y=18 → a>b es false, y<x es false → 'ultimo caso'."""
    ast = build_ast_from_file(PRUEBAS / "pruebaIf.txt")
    result = run(ast)
    assert result.ok
    assert "prueba if" in result.output
    assert "ultimo caso" in result.output


def test_simple_assignment_and_write() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 42;
        write(x);
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["42"]
    assert result.memory["x"] == 42


def test_arithmetic_expression() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 2 + 3 * 4;
        write(x);
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["14"]  # 2 + (3*4) = 14


def test_quadruples_generated() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 5;
        write(x);
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert len(result.quadruples) > 0
    # Al menos := y write
    ops = [q.op for q in result.quadruples]
    assert ":=" in ops
    assert "write" in ops


def test_while_loop() -> None:
    src = """\
program main{
    var n : int;
    begin;
        n := 3;
        while (n >= 1) do {
            write(n);
            n--;
        }
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["3", "2", "1"]


def test_for_loop() -> None:
    src = """\
program main{
    var i : int;
    begin;
        for (i:=0; i < 3; i++) {
            write(i);
        }
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["0", "1", "2"]


def test_if_true_branch() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 10;
        if (x > 5) then {
            write("yes");
        } else {
            write("no");
        }
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["yes"]


def test_if_false_branch() -> None:
    src = """\
program main{
    var x : int;
    begin;
        x := 2;
        if (x > 5) then {
            write("yes");
        } else {
            write("no");
        }
    end;
}"""
    ast = build_ast(src)
    result = run(ast)
    assert result.output == ["no"]
