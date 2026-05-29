"""Robustez de operadores: comparaciones (<=, ==, !=), lógicos (or, not),
aritméticos (/, %) y menos unario.

Cubre las cuatro capas del pipeline para cada operador: léxico → parser →
AST → semántica → ejecución, usando tanto el archivo de prueba completo como
programas mínimos en línea.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from compilador.ast_builder import build_ast, build_ast_from_file
from compilador.contract import TOKEN_TYPES
from compilador.interpreter import run
from compilador.lexer import tokenize, tokenize_file
from compilador.semantic import analyze

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


def _run_src(src: str):
    """Compila y ejecuta un programa; devuelve (output, sem_errors, run_errors)."""
    ast = build_ast(src)
    _, sem_errors = analyze(ast)
    result = run(ast)
    return result.output, sem_errors, result.errors


def _program(body: str, decls: str = "var a, b, r : int;") -> str:
    return f"program main{{\n\t{decls}\n\tbegin;\n{body}\n\tend;\n}}"


# --- Archivo de prueba completo ---------------------------------------------

EXPECTED_OPERADORES = [
    "prueba operadores",
    "22", "12", "85", "3", "2",      # + - * / %
    "-17", "-12", "-85",             # menos unario
    "1", "0", "1", "0", "1", "1",    # > < >= <= == !=
    "1", "1", "1",                   # and or not
    "0", "1", "2", "3",              # while con <=
    "3", "2", "1",                   # for con >= y --
]


def test_prueba_operadores_runs_with_expected_output() -> None:
    ast = build_ast_from_file(PRUEBAS / "pruebaOperadores.txt")
    _, errors = analyze(ast)
    assert errors == []
    result = run(ast)
    assert result.ok
    assert result.output == EXPECTED_OPERADORES


def test_prueba_operadores_lexes_with_known_token_types() -> None:
    tokens = tokenize_file(PRUEBAS / "pruebaOperadores.txt")
    assert len(tokens) > 0
    for t in tokens:
        assert t.type in TOKEN_TYPES, f"tipo desconocido {t.type!r} (actualiza contract.py)"


# --- Léxico: los nuevos terminales existen ----------------------------------

@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("<=", "LE"),
        ("==", "EQ"),
        ("!=", "NE"),
        ("/", "SLASH"),
        ("%", "PERCENT"),
        ("or", "OR"),
        ("not", "NOT"),
    ],
)
def test_new_tokens_lex(text: str, expected_type: str) -> None:
    types = [t.type for t in tokenize(text)]
    assert expected_type in types


# --- Comparaciones -----------------------------------------------------------

@pytest.mark.parametrize(
    ("expr", "truthy"),
    [
        ("3 <= 3", True),
        ("4 <= 3", False),
        ("3 >= 4", False),
        ("5 == 5", True),
        ("5 == 6", False),
        ("5 != 6", True),
        ("5 != 5", False),
        ("2 < 9", True),
        ("9 > 2", True),
    ],
)
def test_comparisons(expr: str, truthy: bool) -> None:
    body = f"\t\tif ({expr}) then {{ write(1); }} else {{ write(0); }}"
    output, sem_errors, run_errors = _run_src(_program(body))
    assert sem_errors == []
    assert run_errors == []
    assert output == ["1" if truthy else "0"]


# --- Operadores lógicos ------------------------------------------------------

@pytest.mark.parametrize(
    ("cond", "truthy"),
    [
        ("1 < 2 and 3 < 4", True),
        ("1 < 2 and 4 < 3", False),
        ("1 > 2 or 3 < 4", True),
        ("1 > 2 or 4 < 3", False),
        ("not (1 < 2)", False),
        ("not (2 < 1)", True),
        ("1 < 2 or 2 < 1 and 3 < 1", True),   # and liga más fuerte que or
        ("not 1 < 2 or 1 < 2", True),          # not liga más fuerte que or
    ],
)
def test_logical_operators(cond: str, truthy: bool) -> None:
    body = f"\t\tif ({cond}) then {{ write(1); }} else {{ write(0); }}"
    output, sem_errors, run_errors = _run_src(_program(body))
    assert sem_errors == []
    assert run_errors == []
    assert output == ["1" if truthy else "0"]


# --- Aritmética: / % y menos unario -----------------------------------------

@pytest.mark.parametrize(
    ("expr", "value"),
    [
        ("17 / 5", "3"),
        ("17 % 5", "2"),
        ("20 / 4", "5"),
        ("20 % 4", "0"),
        ("2 + 3 * 4", "14"),       # * antes que +
        ("(2 + 3) * 4", "20"),
        ("-5", "-5"),
        ("-5 + 2", "-3"),
        ("3 * -2", "-6"),
        ("10 - -4", "14"),
        ("100 / 10 / 2", "5"),     # asociatividad izquierda
    ],
)
def test_arithmetic(expr: str, value: str) -> None:
    body = f"\t\tr := {expr}; write(r);"
    output, sem_errors, run_errors = _run_src(_program(body))
    assert sem_errors == []
    assert run_errors == []
    assert output == [value]


# --- Errores en tiempo de ejecución -----------------------------------------

def test_division_by_zero_runtime() -> None:
    output, sem_errors, run_errors = _run_src(_program("\t\tr := 5 / 0; write(r);"))
    assert sem_errors == []
    assert run_errors
    assert "cero" in run_errors[0].message


def test_modulo_by_zero_runtime() -> None:
    output, sem_errors, run_errors = _run_src(_program("\t\tr := 5 % 0; write(r);"))
    assert sem_errors == []
    assert run_errors
    assert "cero" in run_errors[0].message


# --- Errores semánticos: lógicos sobre enteros ------------------------------

def test_not_on_integer_is_semantic_error() -> None:
    body = "\t\tif (not a) then { write(1); }"
    _, sem_errors, _ = _run_src(_program(body))
    assert any("not" in e.message or "booleano" in e.message for e in sem_errors)


def test_or_with_integer_operand_is_semantic_error() -> None:
    body = "\t\tif (a > 0 or a) then { write(1); }"
    _, sem_errors, _ = _run_src(_program(body))
    assert any("or" in e.message or "booleano" in e.message for e in sem_errors)


# --- Operadores nuevos dentro de control de flujo ---------------------------

def test_while_with_le() -> None:
    body = "\t\tr := 0;\n\t\twhile (r <= 2) do { write(r); r := r + 1; }"
    output, sem_errors, run_errors = _run_src(_program(body))
    assert sem_errors == []
    assert run_errors == []
    assert output == ["0", "1", "2"]


def test_for_with_modulo_in_body() -> None:
    body = (
        "\t\tfor (a := 0; a <= 5; a++) {\n"
        "\t\t\tif (a % 2 == 0) then { write(a); }\n"
        "\t\t}"
    )
    output, sem_errors, run_errors = _run_src(_program(body))
    assert sem_errors == []
    assert run_errors == []
    assert output == ["0", "2", "4"]
