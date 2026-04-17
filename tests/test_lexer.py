"""Pruebas del léxico sobre los archivos del profesor en `pruebas/`."""

from __future__ import annotations

from pathlib import Path

import pytest
from lark import UnexpectedCharacters

from compilador.contract import TOKEN_TYPES
from compilador.lexer import tokenize, tokenize_file

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"


@pytest.mark.parametrize(
    "name",
    ["pruebaFor.txt", "pruebaWhile.txt", "pruebaIf.txt", "pruebaErrores.txt"],
)
def test_pruebas_lex_without_error(name: str) -> None:
    path = PRUEBAS / name
    tokens = tokenize_file(path)
    assert len(tokens) > 0
    for t in tokens:
        assert t.type in TOKEN_TYPES, f"tipo desconocido {t.type!r} (actualiza contract.py)"


def test_prueba_for_has_for_inc_lt() -> None:
    types = [t.type for t in tokenize_file(PRUEBAS / "pruebaFor.txt")]
    assert "FOR" in types
    assert "INC" in types
    assert "LT" in types


def test_prueba_while_has_while_ge_dec() -> None:
    types = [t.type for t in tokenize_file(PRUEBAS / "pruebaWhile.txt")]
    assert "WHILE" in types
    assert "GE" in types
    assert "DEC" in types


def test_prueba_if_has_if_then_else() -> None:
    types = [t.type for t in tokenize_file(PRUEBAS / "pruebaIf.txt")]
    for kw in ("IF", "THEN", "ELSE"):
        assert kw in types


def test_prueba_errores_has_and() -> None:
    types = [t.type for t in tokenize_file(PRUEBAS / "pruebaErrores.txt")]
    assert "AND" in types


def test_invalid_character() -> None:
    with pytest.raises(UnexpectedCharacters):
        tokenize("@ no es parte del lenguaje en fase 1")
