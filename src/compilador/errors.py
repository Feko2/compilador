"""Formato estable de mensajes de error (Fase 0)."""

from __future__ import annotations

from lark import UnexpectedCharacters, UnexpectedInput

from compilador.contract import ERROR_PREFIX


def format_unexpected_characters(exc: UnexpectedCharacters) -> str:
    """Error cuando el léxico no reconoce un carácter en la posición dada."""
    line = exc.line
    column = exc.column
    char = exc.char
    return (
        f"{ERROR_PREFIX}: carácter inesperado {char!r} en línea {line}, columna {column}. "
        f"Opciones esperadas (resumen): {exc.allowed}"
    )


def format_unexpected_input(exc: UnexpectedInput) -> str:
    """Respaldo para errores genéricos de Lark en etapas con parser."""
    return f"{ERROR_PREFIX}: {exc}"
