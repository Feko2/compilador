"""
Fase 0 — contrato léxico derivado solo de `pruebas/*.txt`.

No amplía el lenguaje: cualquier token nuevo en los ejemplos del profesor
debe añadirse aquí y en `lexer/tokens.lark` antes de usarse en fases posteriores.
"""

from __future__ import annotations

# Palabras reservadas que aparecen literalmente en los cuatro archivos de prueba.
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
)

# Operadores y signos de puntuación visibles en esos mismos archivos.
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
    "(",
    ")",
    "{",
    "}",
    ";",
    ",",
    ":",
)

# Nombres de tipo de token que expone el analizador (Lark `Token.type`).
# Útil para tests y para explicar el oral qué sale del léxico.
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
    "ASSIGN",
    "INC",
    "DEC",
    "GE",
    "GT",
    "LT",
    "PLUS",
    "MINUS",
    "STAR",
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
