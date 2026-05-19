"""Formato estable de mensajes de error (Fase 0) y conversión a diagnósticos."""

from __future__ import annotations

from lark import Token, UnexpectedCharacters, UnexpectedInput, UnexpectedToken

from compilador.contract import ERROR_PREFIX
from compilador.diagnostic import Diagnostic


def format_unexpected_characters(exc: UnexpectedCharacters) -> str:
    """Error cuando el léxico no reconoce un carácter en la posición dada."""
    return diagnostic_from_characters(exc).message


def format_unexpected_input(exc: UnexpectedInput) -> str:
    """Mensaje legible para errores del parser u otras fases Lark."""
    return diagnostic_from_input(exc).message


def diagnostic_from_characters(exc: UnexpectedCharacters) -> Diagnostic:
    allowed = ", ".join(sorted(exc.allowed)) if exc.allowed else "(ninguna)"
    return Diagnostic(
        phase="lex",
        line=exc.line,
        column=exc.column,
        message=(
            f"{ERROR_PREFIX}: carácter inesperado {exc.char!r} en línea {exc.line}, "
            f"columna {exc.column}."
        ),
        hint=f"El analizador léxico no reconoce este símbolo. Terminales posibles: {allowed}.",
    )


def diagnostic_from_input(exc: UnexpectedInput) -> Diagnostic:
    if isinstance(exc, UnexpectedToken):
        return _diagnostic_from_unexpected_token(exc)
    line = getattr(exc, "line", 1) or 1
    column = getattr(exc, "column", 1) or 1
    return Diagnostic(
        phase="syntax",
        line=line,
        column=column,
        message=f"{ERROR_PREFIX}: {exc}",
        hint="Revisa la sintaxis en esa posición (¿falta ;, := o una palabra clave?).",
    )


def _diagnostic_from_unexpected_token(exc: UnexpectedToken) -> Diagnostic:
    token = exc.token
    expected = ", ".join(sorted(exc.expected)) if exc.expected else "(desconocido)"
    value = token.value if isinstance(token, Token) else str(token)
    ttype = token.type if isinstance(token, Token) else "?"
    return Diagnostic(
        phase="syntax",
        line=exc.line,
        column=exc.column,
        message=(
            f"{ERROR_PREFIX}: token inesperado {ttype} {value!r} en línea {exc.line}, "
            f"columna {exc.column}."
        ),
        hint=(
            f"Se esperaba uno de: {expected}. "
            "Si usas if/while/for, la gramática actual (Fase 2) aún no los incluye."
        ),
    )
