"""
Fase 5 — Análisis Semántico.

Responsabilidades:
1. Construir la TABLA DE SÍMBOLOS a partir de las declaraciones (var).
2. Verificar que toda variable usada esté declarada.
3. CHEQUEO DE TIPOS:
   - Las expresiones aritméticas (+, -, *) operan sobre enteros → producen int.
   - Las comparaciones (>, <, >=) operan sobre enteros → producen bool.
   - El operador "and" requiere que AMBOS operandos sean booleanos.
   - Si una ExprCond aparece (expresión usada como condición), es error
     porque un int no es un bool. Esto detecta pruebaErrores.txt.
4. Verificar que write() recibe un int o un string (no un bool).

Errores semánticos se reportan como instancias de Diagnostic con phase="semantic".
El análisis NO detiene la ejecución al primer error: recopila todos los que encuentre.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from compilador.ast_nodes import (
    AndCond,
    Assign,
    BinOp,
    Comparison,
    Cond,
    Dec,
    Expr,
    ExprCond,
    For,
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


# =============================================================================
# TABLA DE SÍMBOLOS
# =============================================================================

@dataclass
class Symbol:
    """Entrada en la tabla de símbolos."""
    name: str
    type_name: str   # "int" por ahora (único tipo del lenguaje)
    declared: bool = True


@dataclass
class SymbolTable:
    """Tabla de símbolos: mapea nombres de variables a su tipo.
    
    En este lenguaje solo hay un scope global (no hay funciones).
    """
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def declare(self, name: str, type_name: str) -> None:
        self.symbols[name] = Symbol(name=name, type_name=type_name)

    def lookup(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def is_declared(self, name: str) -> bool:
        return name in self.symbols


# =============================================================================
# TIPOS DEL SISTEMA DE TIPOS (simplificado)
# =============================================================================

# Solo dos tipos posibles en este lenguaje:
TYPE_INT = "int"
TYPE_BOOL = "bool"   # resultado de comparaciones
TYPE_STRING = "string"
TYPE_ERROR = "error"  # usado cuando hay un error, evita cascada


# =============================================================================
# ANALIZADOR SEMÁNTICO
# =============================================================================

@dataclass
class SemanticAnalyzer:
    """Recorre el AST y verifica reglas semánticas.
    
    Acumula errores en self.errors (no lanza excepciones).
    """
    table: SymbolTable = field(default_factory=SymbolTable)
    errors: list[Diagnostic] = field(default_factory=list)

    def _error(self, message: str, hint: str = "") -> None:
        """Registra un error semántico."""
        self.errors.append(Diagnostic(
            phase="semantic",
            line=1,
            column=1,
            message=f"semantic: {message}",
            hint=hint,
        ))

    # --- Punto de entrada ---------------------------------------------------

    def analyze(self, program: Program) -> list[Diagnostic]:
        """Analiza un programa completo. Devuelve lista de errores (vacía si OK)."""
        self._build_symbol_table(program.declarations)
        for stmt in program.body:
            self._check_stmt(stmt)
        return self.errors

    # --- Tabla de símbolos ---------------------------------------------------

    def _build_symbol_table(self, declarations: list[VarDecl]) -> None:
        for decl in declarations:
            if self.table.is_declared(decl.name):
                self._error(
                    f"Variable '{decl.name}' declarada más de una vez.",
                    "Cada variable solo puede declararse una vez en el bloque var.",
                )
            self.table.declare(decl.name, decl.type_name)

    # --- Chequeo de sentencias -----------------------------------------------

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
        if not self.table.is_declared(stmt.target):
            self._error(
                f"Variable '{stmt.target}' no declarada.",
                "Declara la variable en el bloque 'var' antes de usarla.",
            )
        expr_type = self._type_of_expr(stmt.value)
        if expr_type == TYPE_BOOL:
            self._error(
                f"No se puede asignar un valor booleano a '{stmt.target}' (tipo int).",
                "Las comparaciones producen bool, no int.",
            )

    def _check_write(self, stmt: Write) -> None:
        if isinstance(stmt.arg, str):
            return  # string literal — siempre válido
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
            self._error(
                f"Variable '{stmt.target}' no declarada (usada con {op}).",
                "Declara la variable en el bloque 'var'.",
            )

    # --- Chequeo de condiciones ----------------------------------------------

    def _check_condition(self, cond: Cond) -> str:
        """Verifica una condición y devuelve su tipo (debe ser bool)."""
        if isinstance(cond, Comparison):
            left_t = self._type_of_expr(cond.left)
            right_t = self._type_of_expr(cond.right)
            if left_t != TYPE_INT or right_t != TYPE_INT:
                self._error(
                    f"Comparación '{cond.op}' requiere operandos enteros.",
                    "Ambos lados de una comparación deben ser de tipo int.",
                )
            return TYPE_BOOL

        elif isinstance(cond, AndCond):
            left_t = self._check_condition(cond.left)
            right_t = self._check_condition(cond.right)
            if left_t != TYPE_BOOL:
                self._error(
                    "El operando izquierdo de 'and' no es booleano.",
                    "Usa una comparación (>, <, >=) para obtener un valor booleano.",
                )
            if right_t != TYPE_BOOL:
                self._error(
                    "El operando derecho de 'and' no es booleano.",
                    "Usa una comparación (>, <, >=) en lugar de una expresión aritmética.",
                )
            return TYPE_BOOL

        elif isinstance(cond, ExprCond):
            expr_t = self._type_of_expr(cond.expr)
            if expr_t != TYPE_BOOL:
                self._error(
                    "Se usa una expresión entera donde se espera una condición booleana.",
                    "Una expresión aritmética no es una condición válida. "
                    "Usa una comparación como (x > 0) o (x < y).",
                )
                return TYPE_ERROR
            return TYPE_BOOL

        return TYPE_ERROR

    # --- Inferencia de tipos de expresiones ----------------------------------

    def _type_of_expr(self, expr: Expr) -> str:
        """Devuelve el tipo de una expresión; reporta errores si hay variables no declaradas."""
        if isinstance(expr, IntLit):
            return TYPE_INT

        elif isinstance(expr, Var):
            if not self.table.is_declared(expr.name):
                self._error(
                    f"Variable '{expr.name}' no declarada.",
                    "Declara la variable en el bloque 'var' antes de usarla.",
                )
                return TYPE_ERROR
            return self.table.lookup(expr.name).type_name

        elif isinstance(expr, BinOp):
            left_t = self._type_of_expr(expr.left)
            right_t = self._type_of_expr(expr.right)
            if left_t != TYPE_INT or right_t != TYPE_INT:
                if left_t != TYPE_ERROR and right_t != TYPE_ERROR:
                    self._error(
                        f"Operador '{expr.op}' requiere operandos enteros.",
                        "Las operaciones aritméticas solo funcionan con int.",
                    )
                return TYPE_ERROR
            return TYPE_INT

        return TYPE_ERROR


# =============================================================================
# API PÚBLICA
# =============================================================================

def analyze(program: Program) -> tuple[SymbolTable, list[Diagnostic]]:
    """Ejecuta el análisis semántico completo.
    
    Devuelve:
        - La tabla de símbolos construida
        - Lista de errores semánticos (vacía si todo está bien)
    """
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(program)
    return analyzer.table, errors
