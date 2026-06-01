"""
Árbol de Sintaxis Abstracta (AST).

Nodos principales:
    Program
    ├── declarations: VarDecl (int o array [N] of int)
    ├── functions: FunctionDef
    └── body: sentencias del begin/end principal

Expresiones extra:
    - ArrayAccess: arr[i]
    - Call: f(a, b)

Asignación:
    - target puede ser str (variable) o ArrayAccess (elemento de arreglo)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# =============================================================================
# EXPRESIONES ARITMÉTICAS
# =============================================================================

@dataclass(frozen=True)
class Var:
    """Referencia a una variable escalar."""
    name: str


@dataclass(frozen=True)
class IntLit:
    """Literal entero."""
    value: int


@dataclass(frozen=True)
class BinOp:
    """Operación binaria: left OP right (+, -, *)."""
    op: str
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class ArrayAccess:
    """Acceso a arreglo: nombre[index]. Índices válidos: 0 .. tamaño-1."""
    name: str
    index: "Expr"


@dataclass(frozen=True)
class Call:
    """Llamada a función: nombre(arg1, arg2, ...)."""
    name: str
    args: tuple["Expr", ...] = ()


Expr = Union[Var, IntLit, BinOp, ArrayAccess, Call]
# Un lvalue válido es una variable (str) o un elemento de arreglo (ArrayAccess).
# IntLit se admite solo para reportar "lvalue inválido" en el análisis semántico.
LValue = Union[str, ArrayAccess, IntLit]


# =============================================================================
# CONDICIONES
# =============================================================================

@dataclass(frozen=True)
class Comparison:
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class AndCond:
    left: "Cond"
    right: "Cond"


@dataclass(frozen=True)
class OrCond:
    left: "Cond"
    right: "Cond"


@dataclass(frozen=True)
class NotCond:
    operand: "Cond"


@dataclass(frozen=True)
class ExprCond:
    expr: Expr


Cond = Union[Comparison, AndCond, OrCond, NotCond, ExprCond]


# =============================================================================
# SENTENCIAS
# =============================================================================

@dataclass(frozen=True)
class Assign:
    """Asignación: target := value (target escalar o arr[i])."""
    target: LValue
    value: Expr


@dataclass(frozen=True)
class CallStmt:
    """Llamada a función usada como sentencia: proc(); (descarta el retorno)."""
    call: Call


@dataclass(frozen=True)
class Write:
    arg: Union[Expr, str]


@dataclass(frozen=True)
class If:
    condition: Cond
    then_body: list["Stmt"]
    else_body: list["Stmt"] = field(default_factory=list)


@dataclass(frozen=True)
class While:
    condition: Cond
    body: list["Stmt"]


@dataclass(frozen=True)
class For:
    init: Assign
    condition: Cond
    update: "Stmt"
    body: list["Stmt"]


@dataclass(frozen=True)
class Inc:
    target: str


@dataclass(frozen=True)
class Dec:
    target: str


Stmt = Union[Assign, CallStmt, Write, If, While, For, Inc, Dec]


# =============================================================================
# DECLARACIONES Y FUNCIONES
# =============================================================================

@dataclass(frozen=True)
class VarDecl:
    """Declaración de variable escalar o arreglo."""
    name: str
    type_name: str = "int"
    array_size: int | None = None  # None = escalar; N = array [N] of int


@dataclass(frozen=True)
class Param:
    name: str
    type_name: str = "int"


@dataclass(frozen=True)
class FunctionDef:
    """Definición de función con cuerpo begin/end."""
    name: str
    params: tuple[Param, ...]
    return_type: str
    body: list[Stmt]


@dataclass
class Program:
    declarations: list[VarDecl]
    functions: list[FunctionDef] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)
