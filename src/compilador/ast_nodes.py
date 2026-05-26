"""
Fase 4 — Árbol de Sintaxis Abstracta (AST).

Define los nodos del AST como dataclasses inmutables. Cada nodo representa
una construcción semántica del lenguaje (no un detalle sintáctico como
paréntesis o punto y coma).

Jerarquía principal:
    Program
    └── declarations: lista de variables
    └── body: lista de Statement

Statement (sentencias):
    - Assign: variable := expresión
    - Write: write(argumento)
    - If: condición + bloque then + bloque else opcional
    - While: condición + cuerpo
    - For: init + condición + update + cuerpo
    - Inc / Dec: variable++ o variable--

Expr (expresiones aritméticas):
    - BinOp: operación binaria (+, -, *)
    - Var: referencia a variable
    - IntLit: literal entero

Condition (expresiones booleanas):
    - Comparison: expr OP expr (>, <, >=)
    - AndCond: condición AND condición
    - ExprCond: expresión usada como condición (error semántico potencial)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# =============================================================================
# EXPRESIONES ARITMÉTICAS
# =============================================================================

@dataclass(frozen=True)
class Var:
    """Referencia a una variable por nombre."""
    name: str


@dataclass(frozen=True)
class IntLit:
    """Literal entero (e.g. 5, 100)."""
    value: int


@dataclass(frozen=True)
class BinOp:
    """Operación binaria: left OP right (donde OP es +, - o *)."""
    op: str       # "+", "-", "*"
    left: "Expr"
    right: "Expr"


# Tipo unión para todas las expresiones
Expr = Union[Var, IntLit, BinOp]


# =============================================================================
# CONDICIONES (expresiones booleanas)
# =============================================================================

@dataclass(frozen=True)
class Comparison:
    """Comparación: left OP right (donde OP es >, < o >=)."""
    op: str       # ">", "<", ">="
    left: Expr
    right: Expr


@dataclass(frozen=True)
class AndCond:
    """Conjunción lógica: left AND right."""
    left: "Cond"
    right: "Cond"


@dataclass(frozen=True)
class ExprCond:
    """Expresión usada como condición (e.g. (a*5+(b+4))).
    
    Esto es un ERROR SEMÁNTICO si la expresión no es booleana.
    La gramática lo permite para poder parsear pruebaErrores.txt
    y luego reportar el error en la fase semántica.
    """
    expr: Expr


# Tipo unión para todas las condiciones
Cond = Union[Comparison, AndCond, ExprCond]


# =============================================================================
# SENTENCIAS (statements)
# =============================================================================

@dataclass(frozen=True)
class Assign:
    """Asignación: variable := expresión."""
    target: str
    value: Expr


@dataclass(frozen=True)
class Write:
    """Sentencia write: imprime una expresión o un string literal."""
    arg: Union[Expr, str]  # str si es un literal de cadena


@dataclass(frozen=True)
class If:
    """Sentencia if/then/else."""
    condition: Cond
    then_body: list["Stmt"]
    else_body: list["Stmt"] = field(default_factory=list)


@dataclass(frozen=True)
class While:
    """Sentencia while/do."""
    condition: Cond
    body: list["Stmt"]


@dataclass(frozen=True)
class For:
    """Sentencia for(init; cond; update) { body }.
    
    init: asignación inicial (e.g. i := 1)
    update: puede ser Inc, Dec o Assign
    """
    init: Assign
    condition: Cond
    update: "Stmt"
    body: list["Stmt"]


@dataclass(frozen=True)
class Inc:
    """Post-incremento: variable++."""
    target: str


@dataclass(frozen=True)
class Dec:
    """Post-decremento: variable--."""
    target: str


# Tipo unión para todas las sentencias
Stmt = Union[Assign, Write, If, While, For, Inc, Dec]


# =============================================================================
# PROGRAMA (nodo raíz)
# =============================================================================

@dataclass(frozen=True)
class VarDecl:
    """Declaración de variable con su tipo."""
    name: str
    type_name: str  # "int" por ahora


@dataclass
class Program:
    """Nodo raíz: un programa completo.
    
    declarations: variables declaradas en el bloque var
    body: lista de sentencias entre begin; y end;
    """
    declarations: list[VarDecl]
    body: list[Stmt]
