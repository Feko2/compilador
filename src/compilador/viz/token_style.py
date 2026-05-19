"""Clases CSS por tipo de token para el informe HTML."""

from __future__ import annotations

_KEYWORDS = frozenset(
    {
        "PROGRAM",
        "MAIN",
        "VAR",
        "INT_KW",
        "BEGIN",
        "END",
        "WRITE",
        "WHILE",
        "DO",
        "IF",
        "THEN",
        "ELSE",
        "FOR",
        "AND",
    }
)

_OPERATORS = frozenset(
    {
        "ASSIGN",
        "INC",
        "DEC",
        "GE",
        "GT",
        "LT",
        "PLUS",
        "MINUS",
        "STAR",
    }
)

_PUNCT = frozenset(
    {
        "LPAR",
        "RPAR",
        "LBRACE",
        "RBRACE",
        "SEMICOLON",
        "COMMA",
        "COLON",
    }
)


def css_class_for_token(token_type: str) -> str:
    if token_type in _KEYWORDS:
        return "tok-keyword"
    if token_type in _OPERATORS:
        return "tok-operator"
    if token_type in _PUNCT:
        return "tok-punct"
    if token_type == "IDENT":
        return "tok-ident"
    if token_type == "INTEGER":
        return "tok-integer"
    if token_type == "STRING":
        return "tok-string"
    return "tok-other"
