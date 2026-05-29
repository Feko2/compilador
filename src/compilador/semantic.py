"""
Fase 5 — Análisis Semántico (con arreglos y funciones).

Tabla de símbolos global + ámbitos locales en funciones.
Chequeos extra:
- array [N] of int: un solo nombre por declaración
- arr[i]: i entero, arr declarado como arreglo, bounds en runtime
- function f(a: int): cuerpo con f := expr como retorno
- llamada f(x, y): existe, argumentos int, cantidad correcta
"""

from __future__ import annotations

from dataclasses import dataclass, field

from compilador.ast_nodes import (
    AndCond,
    ArrayAccess,
    Assign,
    BinOp,
    Call,
    Comparison,
    Cond,
    Dec,
    Expr,
    ExprCond,
    For,
    FunctionDef,
    If,
    Inc,
    IntLit,
    Program,
    Stmt,
    Var,
    VarDecl,
    While,
    Write,
)
from compilador.diagnostic import Diagnostic

TYPE_INT = "int"
TYPE_ARRAY = "int[]"
TYPE_BOOL = "bool"
TYPE_ERROR = "error"


@dataclass
class Symbol:
    name: str
    type_name: str
    array_size: int | None = None


@dataclass
class SymbolTable:
    symbols: dict[str, Symbol] = field(default_factory=dict)
    functions: dict[str, FunctionDef] = field(default_factory=dict)

    def declare(self, name: str, type_name: str, *, array_size: int | None = None) -> None:
        self.symbols[name] = Symbol(name=name, type_name=type_name, array_size=array_size)

    def lookup(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def is_declared(self, name: str) -> bool:
        return name in self.symbols

    def copy(self) -> SymbolTable:
        return SymbolTable(
            symbols=dict(self.symbols),
            functions=dict(self.functions),
        )


@dataclass
class SemanticAnalyzer:
    table: SymbolTable = field(default_factory=SymbolTable)
    errors: list[Diagnostic] = field(default_factory=list)
    _current_function: str | None = None

    def _error(self, message: str, hint: str = "") -> None:
        self.errors.append(Diagnostic(
            phase="semantic",
            line=1,
            column=1,
            message=f"semantic: {message}",
            hint=hint,
        ))

    def analyze(self, program: Program) -> list[Diagnostic]:
        for func in program.functions:
            if func.name in self.table.functions:
                self._error(f"Función '{func.name}' definida más de una vez.")
            self.table.functions[func.name] = func

        self._build_symbol_table(program.declarations)
        for func in program.functions:
            self._analyze_function(func)
        for stmt in program.body:
            self._check_stmt(stmt)
        return self.errors

    def _build_symbol_table(self, declarations: list[VarDecl]) -> None:
        for decl in declarations:
            if self.table.is_declared(decl.name):
                self._error(f"Variable '{decl.name}' declarada más de una vez.")
            if decl.array_size is not None and decl.array_size <= 0:
                self._error(
                    f"Tamaño inválido para arreglo '{decl.name}'.",
                    "Usa un entero positivo: array [N] of int.",
                )
            self.table.declare(
                decl.name,
                TYPE_ARRAY if decl.array_size else TYPE_INT,
                array_size=decl.array_size,
            )

    def _analyze_function(self, func: FunctionDef) -> None:
        local = self.table.copy()
        local.symbols = dict(self.table.symbols)
        saved_table = self.table
        saved_fn = self._current_function
        self.table = local
        self._current_function = func.name

        for param in func.params:
            if self.table.is_declared(param.name):
                self._error(f"Parámetro '{param.name}' oculta una variable global.")
            self.table.declare(param.name, TYPE_INT)
        self.table.declare(func.name, TYPE_INT)

        for stmt in func.body:
            self._check_stmt(stmt)

        self.table = saved_table
        self._current_function = saved_fn

    def _check_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, Assign):
            self._check_assign(stmt)
        elif isinstance(stmt, Write):
            self._check_write(stmt)
        elif isinstance(stmt, If):
            self._check_if(stmt)
        elif isinstance(stmt, While):
            self._check_while(stmt)
        elif isinstance(stmt, For):
            self._check_for(stmt)
        elif isinstance(stmt, (Inc, Dec)):
            self._check_inc_dec(stmt)

    def _check_assign(self, stmt: Assign) -> None:
        value_type = self._type_of_expr(stmt.value)
        if value_type == TYPE_BOOL:
            self._error("No se puede asignar un valor booleano a una variable int.")

        if isinstance(stmt.target, str):
            if stmt.target == self._current_function:
                return
            if not self.table.is_declared(stmt.target):
                self._error(f"Variable '{stmt.target}' no declarada.")
                return
            sym = self.table.lookup(stmt.target)
            if sym and sym.type_name == TYPE_ARRAY:
                self._error(
                    f"'{stmt.target}' es un arreglo; usa '{stmt.target}[i] := valor'.",
                )
        elif isinstance(stmt.target, ArrayAccess):
            self._check_array_access(stmt.target, for_write=True)

    def _check_write(self, stmt: Write) -> None:
        if isinstance(stmt.arg, str):
            return
        self._type_of_expr(stmt.arg)

    def _check_if(self, stmt: If) -> None:
        self._check_condition(stmt.condition)
        for s in stmt.then_body:
            self._check_stmt(s)
        for s in stmt.else_body:
            self._check_stmt(s)

    def _check_while(self, stmt: While) -> None:
        self._check_condition(stmt.condition)
        for s in stmt.body:
            self._check_stmt(s)

    def _check_for(self, stmt: For) -> None:
        self._check_assign(stmt.init)
        self._check_condition(stmt.condition)
        self._check_stmt(stmt.update)
        for s in stmt.body:
            self._check_stmt(s)

    def _check_inc_dec(self, stmt: Inc | Dec) -> None:
        if not self.table.is_declared(stmt.target):
            op = "++" if isinstance(stmt, Inc) else "--"
            self._error(f"Variable '{stmt.target}' no declarada (usada con {op}).")
            return
        sym = self.table.lookup(stmt.target)
        if sym and sym.type_name == TYPE_ARRAY:
            self._error(f"No se puede usar ++/-- sobre el arreglo '{stmt.target}'.")

    def _check_array_access(self, access: ArrayAccess, *, for_write: bool = False) -> None:
        if not self.table.is_declared(access.name):
            self._error(f"Arreglo '{access.name}' no declarado.")
            return
        sym = self.table.lookup(access.name)
        if sym and sym.type_name != TYPE_ARRAY:
            self._error(f"'{access.name}' no es un arreglo.")
        idx_type = self._type_of_expr(access.index)
        if idx_type != TYPE_INT:
            self._error("El índice de un arreglo debe ser entero.")

    def _check_call(self, call: Call) -> str:
        func = self.table.functions.get(call.name)
        if func is None:
            self._error(
                f"Función '{call.name}' no definida.",
                "Declara la función antes del begin; del programa principal.",
            )
            return TYPE_ERROR
        if len(call.args) != len(func.params):
            self._error(
                f"Función '{call.name}' espera {len(func.params)} argumento(s), "
                f"recibió {len(call.args)}.",
            )
        for arg in call.args:
            arg_type = self._type_of_expr(arg)
            if arg_type != TYPE_INT:
                self._error(f"Argumento de '{call.name}' debe ser int.")
        return TYPE_INT

    def _check_condition(self, cond: Cond) -> str:
        if isinstance(cond, Comparison):
            left_t = self._type_of_expr(cond.left)
            right_t = self._type_of_expr(cond.right)
            if left_t not in (TYPE_INT, TYPE_ERROR) or right_t not in (TYPE_INT, TYPE_ERROR):
                self._error(f"Comparación '{cond.op}' requiere operandos enteros.")
            return TYPE_BOOL

        if isinstance(cond, AndCond):
            left_t = self._check_condition(cond.left)
            right_t = self._check_condition(cond.right)
            if left_t != TYPE_BOOL:
                self._error("El operando izquierdo de 'and' no es booleano.")
            if right_t != TYPE_BOOL:
                self._error("El operando derecho de 'and' no es booleano.")
            return TYPE_BOOL

        if isinstance(cond, ExprCond):
            expr_t = self._type_of_expr(cond.expr)
            if expr_t != TYPE_BOOL:
                self._error(
                    "Se usa una expresión entera donde se espera una condición booleana.",
                )
                return TYPE_ERROR
            return TYPE_BOOL

        return TYPE_ERROR

    def _type_of_expr(self, expr: Expr) -> str:
        if isinstance(expr, IntLit):
            return TYPE_INT

        if isinstance(expr, Var):
            if not self.table.is_declared(expr.name):
                self._error(f"Variable '{expr.name}' no declarada.")
                return TYPE_ERROR
            sym = self.table.lookup(expr.name)
            if sym and sym.type_name == TYPE_ARRAY:
                self._error(
                    f"'{expr.name}' es un arreglo; usa '{expr.name}[i]' para leer un elemento.",
                )
                return TYPE_ERROR
            return TYPE_INT

        if isinstance(expr, ArrayAccess):
            self._check_array_access(expr)
            return TYPE_INT

        if isinstance(expr, Call):
            return self._check_call(expr)

        if isinstance(expr, BinOp):
            left_t = self._type_of_expr(expr.left)
            right_t = self._type_of_expr(expr.right)
            if left_t != TYPE_INT or right_t != TYPE_INT:
                if TYPE_ERROR not in (left_t, right_t):
                    self._error(f"Operador '{expr.op}' requiere operandos enteros.")
                return TYPE_ERROR
            return TYPE_INT

        return TYPE_ERROR


def analyze(program: Program) -> tuple[SymbolTable, list[Diagnostic]]:
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(program)
    return analyzer.table, errors
