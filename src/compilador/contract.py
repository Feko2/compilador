"""
Contrato léxico del lenguaje del compilador.

Incluye tokens de pruebas/*.txt y
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
    "or",
    "not",
    # Extra — arreglos y funciones
    "array",
    "of",
    "function",
)

PUNCTUATION_AND_OPERATORS: tuple[str, ...] = (
    ":=",
    "++",
    "--",
    "==",
    "!=",
    ">=",
    "<=",
    ">",
    "<",
    "+",
    "-",
    "*",
    "/",
    "%",
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
    "OR",
    "NOT",
    "ARRAY",
    "OF",
    "FUNCTION",
    "ASSIGN",
    "INC",
    "DEC",
    "EQ",
    "NE",
    "GE",
    "LE",
    "GT",
    "LT",
    "PLUS",
    "MINUS",
    "STAR",
    "SLASH",
    "PERCENT",
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
