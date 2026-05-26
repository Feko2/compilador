"""
Fase 6–7 — Intérprete (Runtime).

Ejecuta un AST de forma directa (tree-walking interpreter). Este enfoque
es equivalente a tener un IR implícito: el AST ES la representación intermedia
y lo evaluamos nodo por nodo.

Para fines académicos, también generamos CUÁDRUPLOS (IR) durante la ejecución,
que se pueden mostrar en el informe HTML. Los cuádruplos siguen el formato:
    (operador, arg1, arg2, resultado)

Arquitectura del intérprete:
    - Memoria: diccionario variable → valor (enteros)
    - Salida: lista de strings (lo que produce write())
    - Evaluación: recursiva sobre los nodos del AST

El intérprete ASUME que el análisis semántico ya pasó sin errores.
Si se ejecuta un programa con errores semánticos, el comportamiento
es indefinido (puede lanzar RuntimeError).
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
    While,
    Write,
)
from compilador.diagnostic import Diagnostic
from compilador.models import MemoryCell, Quadruple


# =============================================================================
# RESULTADO DE LA EJECUCIÓN
# =============================================================================

@dataclass
class ExecutionResult:
    """Resultado completo de ejecutar un programa."""
    output: list[str] = field(default_factory=list)
    memory: dict[str, int] = field(default_factory=dict)
    quadruples: list[Quadruple] = field(default_factory=list)
    errors: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# =============================================================================
# INTÉRPRETE
# =============================================================================

@dataclass
class Interpreter:
    """Intérprete tree-walking del AST.
    
    Evalúa el programa y produce:
    - output: líneas impresas por write()
    - memory: estado final de las variables
    - quadruples: cuádruplos generados (IR para el informe)
    """
    memory: dict[str, int] = field(default_factory=dict)
    output: list[str] = field(default_factory=list)
    quadruples: list[Quadruple] = field(default_factory=list)
    _temp_counter: int = 0

    def _new_temp(self) -> str:
        """Genera un nombre de temporal para cuádruplos (T1, T2, ...)."""
        self._temp_counter += 1
        return f"T{self._temp_counter}"

    def _emit(self, op: str, arg1: str, arg2: str, result: str) -> None:
        """Emite un cuádruplo al registro de IR."""
        idx = len(self.quadruples) + 1
        self.quadruples.append(Quadruple(index=idx, op=op, arg1=arg1, arg2=arg2, result=result))

    # --- Punto de entrada ---------------------------------------------------

    def execute(self, program: Program) -> ExecutionResult:
        """Ejecuta un programa completo."""
        # Inicializar memoria con las variables declaradas (valor 0 por defecto)
        for decl in program.declarations:
            self.memory[decl.name] = 0

        # Ejecutar las sentencias del cuerpo
        errors: list[Diagnostic] = []
        try:
            for stmt in program.body:
                self._exec_stmt(stmt)
        except RuntimeError as e:
            errors.append(Diagnostic(
                phase="runtime",
                line=1,
                column=1,
                message=f"runtime: {e}",
                hint="Error durante la ejecución del programa.",
            ))

        return ExecutionResult(
            output=self.output,
            memory=dict(self.memory),
            quadruples=self.quadruples,
            errors=errors,
        )

    # --- Ejecución de sentencias ---------------------------------------------

    def _exec_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, Assign):
            self._exec_assign(stmt)
        elif isinstance(stmt, Write):
            self._exec_write(stmt)
        elif isinstance(stmt, If):
            self._exec_if(stmt)
        elif isinstance(stmt, While):
            self._exec_while(stmt)
        elif isinstance(stmt, For):
            self._exec_for(stmt)
        elif isinstance(stmt, Inc):
            self._exec_inc(stmt)
        elif isinstance(stmt, Dec):
            self._exec_dec(stmt)

    def _exec_assign(self, stmt: Assign) -> None:
        value = self._eval_expr(stmt.value)
        self.memory[stmt.target] = value
        self._emit(":=", str(value), "", stmt.target)

    def _exec_write(self, stmt: Write) -> None:
        if isinstance(stmt.arg, str):
            self.output.append(stmt.arg)
            self._emit("write", f'"{stmt.arg}"', "", "stdout")
        else:
            value = self._eval_expr(stmt.arg)
            self.output.append(str(value))
            self._emit("write", str(value), "", "stdout")

    def _exec_if(self, stmt: If) -> None:
        cond_val = self._eval_condition(stmt.condition)
        self._emit("if_false", str(cond_val), "", "goto_else")
        if cond_val:
            for s in stmt.then_body:
                self._exec_stmt(s)
        else:
            for s in stmt.else_body:
                self._exec_stmt(s)

    def _exec_while(self, stmt: While) -> None:
        self._emit("label", "while_start", "", "")
        while self._eval_condition(stmt.condition):
            for s in stmt.body:
                self._exec_stmt(s)
        self._emit("label", "while_end", "", "")

    def _exec_for(self, stmt: For) -> None:
        # Ejecutar inicialización
        self._exec_assign(stmt.init)
        self._emit("label", "for_start", "", "")
        # Loop: evaluar condición, ejecutar cuerpo, ejecutar update
        while self._eval_condition(stmt.condition):
            for s in stmt.body:
                self._exec_stmt(s)
            self._exec_stmt(stmt.update)
        self._emit("label", "for_end", "", "")

    def _exec_inc(self, stmt: Inc) -> None:
        self.memory[stmt.target] += 1
        self._emit("+", stmt.target, "1", stmt.target)

    def _exec_dec(self, stmt: Dec) -> None:
        self.memory[stmt.target] -= 1
        self._emit("-", stmt.target, "1", stmt.target)

    # --- Evaluación de condiciones -------------------------------------------

    def _eval_condition(self, cond: Cond) -> bool:
        if isinstance(cond, Comparison):
            left = self._eval_expr(cond.left)
            right = self._eval_expr(cond.right)
            t = self._new_temp()
            self._emit(cond.op, str(left), str(right), t)
            if cond.op == ">":
                return left > right
            elif cond.op == "<":
                return left < right
            elif cond.op == ">=":
                return left >= right
            raise RuntimeError(f"Operador de comparación desconocido: {cond.op}")

        elif isinstance(cond, AndCond):
            left_val = self._eval_condition(cond.left)
            right_val = self._eval_condition(cond.right)
            t = self._new_temp()
            self._emit("and", str(left_val), str(right_val), t)
            return left_val and right_val

        elif isinstance(cond, ExprCond):
            # Expresión usada como condición — evalúa como "truthy" (!=0)
            val = self._eval_expr(cond.expr)
            return val != 0

        raise RuntimeError(f"Tipo de condición desconocido: {type(cond)}")

    # --- Evaluación de expresiones -------------------------------------------

    def _eval_expr(self, expr: Expr) -> int:
        if isinstance(expr, IntLit):
            return expr.value

        elif isinstance(expr, Var):
            if expr.name not in self.memory:
                raise RuntimeError(f"Variable '{expr.name}' no inicializada.")
            return self.memory[expr.name]

        elif isinstance(expr, BinOp):
            left = self._eval_expr(expr.left)
            right = self._eval_expr(expr.right)
            t = self._new_temp()
            self._emit(expr.op, str(left), str(right), t)
            if expr.op == "+":
                return left + right
            elif expr.op == "-":
                return left - right
            elif expr.op == "*":
                return left * right
            raise RuntimeError(f"Operador aritmético desconocido: {expr.op}")

        raise RuntimeError(f"Tipo de expresión desconocido: {type(expr)}")


# =============================================================================
# API PÚBLICA
# =============================================================================

def run(program: Program) -> ExecutionResult:
    """Ejecuta un programa y devuelve el resultado."""
    interpreter = Interpreter()
    return interpreter.execute(program)
