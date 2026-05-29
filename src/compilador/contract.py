"""
Fase 0 — contrato léxico del lenguaje del compilador.

Incluye tokens de pruebas/*.txt (Fases 0–3) y extensiones extra:
- arreglos: array, of, [ ]
- funciones: function
"""

from __future__ import annotations

KEYWORDS: tuple[str, ...] = (
    "program",
    "main",
    "var",
    "int",
    "begin",
    "end",
    "write",
    "while",
    "do",
    "if",
    "then",
    "else",
    "for",
    "and",
    # Extra — arreglos y funciones
    "array",
    "of",
    "function",
)

PUNCTUATION_AND_OPERATORS: tuple[str, ...] = (
    ":=",
    "++",
    "--",
    ">=",
    ">",
    "<",
    "+",
    "-",
    "*",
    "[",
    "]",
    "(",
    ")",
    "{",
    "}",
    ";",
    ",",
    ":",
)

TOKEN_TYPES: tuple[str, ...] = (
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
    "ARRAY",
    "OF",
    "FUNCTION",
    "ASSIGN",
    "INC",
    "DEC",
    "GE",
    "GT",
    "LT",
    "PLUS",
    "MINUS",
    "STAR",
    "LBRACK",
    "RBRACK",
    "LPAR",
    "RPAR",
    "LBRACE",
    "RBRACE",
    "SEMICOLON",
    "COMMA",
    "COLON",
    "IDENT",
    "INTEGER",
    "STRING",
)

ERROR_PREFIX = "lex"
