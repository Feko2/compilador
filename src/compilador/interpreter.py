"""
Fase 6–7 — Intérprete (Runtime) con arreglos y funciones.

Memoria:
- Escalares: dict[str, int]
- Arreglos: dict[str, list[int]]  (índices 0 .. N-1)

Funciones:
- Se definen en program.functions
- Retorno: asignación al nombre de la función (estilo Pascal)
- Ámbito local: solo parámetros + variable de retorno
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

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
    LValue,
    Program,
    Stmt,
    Var,
    While,
    Write,
)
from compilador.diagnostic import Diagnostic
from compilador.models import Quadruple

Value = int


@dataclass
class ExecutionResult:
    output: list[str] = field(default_factory=list)
    memory: dict[str, Union[int, list[int]]] = field(default_factory=dict)
    quadruples: list[Quadruple] = field(default_factory=list)
    errors: list[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class Interpreter:
    scalars: dict[str, int] = field(default_factory=dict)
    arrays: dict[str, list[int]] = field(default_factory=dict)
    functions: dict[str, FunctionDef] = field(default_factory=dict)
    output: list[str] = field(default_factory=list)
    quadruples: list[Quadruple] = field(default_factory=list)
    _temp_counter: int = 0
    _current_function: str | None = None

    def _new_temp(self) -> str:
        self._temp_counter += 1
        return f"T{self._temp_counter}"

    def _emit(self, op: str, arg1: str, arg2: str, result: str) -> None:
        idx = len(self.quadruples) + 1
        self.quadruples.append(Quadruple(index=idx, op=op, arg1=arg1, arg2=arg2, result=result))

    def execute(self, program: Program) -> ExecutionResult:
        self.functions = {f.name: f for f in program.functions}

        for decl in program.declarations:
            if decl.array_size is not None:
                self.arrays[decl.name] = [0] * decl.array_size
            else:
                self.scalars[decl.name] = 0

        errors: list[Diagnostic] = []
        try:
            for stmt in program.body:
                self._exec_stmt(stmt)
        except RuntimeError as exc:
            errors.append(Diagnostic(
                phase="runtime",
                line=1,
                column=1,
                message=f"runtime: {exc}",
                hint="Error durante la ejecución del programa.",
            ))

        memory: dict[str, Union[int, list[int]]] = dict(self.scalars)
        memory.update(self.arrays)
        return ExecutionResult(
            output=self.output,
            memory=memory,
            quadruples=self.quadruples,
            errors=errors,
        )

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
        if isinstance(stmt.target, str):
            self.scalars[stmt.target] = value
            self._emit(":=", str(value), "", stmt.target)
        elif isinstance(stmt.target, ArrayAccess):
            arr, idx = self._resolve_array(stmt.target)
            arr[idx] = value
            self._emit("[]:=", str(value), f"{stmt.target.name}[{idx}]", stmt.target.name)

    def _exec_write(self, stmt: Write) -> None:
        if isinstance(stmt.arg, str):
            self.output.append(stmt.arg)
            self._emit("write", f'"{stmt.arg}"', "", "stdout")
        else:
            value = self._eval_expr(stmt.arg)
            self.output.append(str(value))
            self._emit("write", str(value), "", "stdout")

    def _exec_if(self, stmt: If) -> None:
        if self._eval_condition(stmt.condition):
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
        self._exec_assign(stmt.init)
        self._emit("label", "for_start", "", "")
        while self._eval_condition(stmt.condition):
            for s in stmt.body:
                self._exec_stmt(s)
            self._exec_stmt(stmt.update)
        self._emit("label", "for_end", "", "")

    def _exec_inc(self, stmt: Inc) -> None:
        self.scalars[stmt.target] += 1
        self._emit("+", stmt.target, "1", stmt.target)

    def _exec_dec(self, stmt: Dec) -> None:
        self.scalars[stmt.target] -= 1
        self._emit("-", stmt.target, "1", stmt.target)

    def _eval_condition(self, cond: Cond) -> bool:
        if isinstance(cond, Comparison):
            left = self._eval_expr(cond.left)
            right = self._eval_expr(cond.right)
            t = self._new_temp()
            self._emit(cond.op, str(left), str(right), t)
            if cond.op == ">":
                return left > right
            if cond.op == "<":
                return left < right
            if cond.op == ">=":
                return left >= right
            raise RuntimeError(f"Operador de comparación desconocido: {cond.op}")

        if isinstance(cond, AndCond):
            return self._eval_condition(cond.left) and self._eval_condition(cond.right)

        if isinstance(cond, ExprCond):
            return self._eval_expr(cond.expr) != 0

        raise RuntimeError(f"Tipo de condición desconocido: {type(cond)}")

    def _eval_expr(self, expr: Expr) -> int:
        if isinstance(expr, IntLit):
            return expr.value

        if isinstance(expr, Var):
            if expr.name not in self.scalars:
                raise RuntimeError(f"Variable '{expr.name}' no inicializada.")
            return self.scalars[expr.name]

        if isinstance(expr, ArrayAccess):
            arr, idx = self._resolve_array(expr)
            self._emit("[]", expr.name, str(idx), f"{expr.name}[{idx}]")
            return arr[idx]

        if isinstance(expr, Call):
            return self._eval_call(expr)

        if isinstance(expr, BinOp):
            left = self._eval_expr(expr.left)
            right = self._eval_expr(expr.right)
            t = self._new_temp()
            self._emit(expr.op, str(left), str(right), t)
            if expr.op == "+":
                return left + right
            if expr.op == "-":
                return left - right
            if expr.op == "*":
                return left * right
            raise RuntimeError(f"Operador aritmético desconocido: {expr.op}")

        raise RuntimeError(f"Tipo de expresión desconocido: {type(expr)}")

    def _resolve_array(self, access: ArrayAccess) -> tuple[list[int], int]:
        if access.name not in self.arrays:
            raise RuntimeError(f"Arreglo '{access.name}' no declarado.")
        idx = self._eval_expr(access.index)
        arr = self.arrays[access.name]
        if idx < 0 or idx >= len(arr):
            raise RuntimeError(
                f"Índice {idx} fuera de rango para '{access.name}' (0..{len(arr) - 1}).",
            )
        return arr, idx

    def _eval_call(self, call: Call) -> int:
        func = self.functions.get(call.name)
        if func is None:
            raise RuntimeError(f"Función '{call.name}' no definida.")

        if len(call.args) != len(func.params):
            raise RuntimeError(
                f"Función '{call.name}' espera {len(func.params)} argumento(s).",
            )

        callee = Interpreter(
            functions=self.functions,
            quadruples=self.quadruples,
        )
        callee._temp_counter = self._temp_counter

        for param, arg_expr in zip(func.params, call.args):
            callee.scalars[param.name] = self._eval_expr(arg_expr)
        callee.scalars[func.name] = 0
        callee._current_function = func.name

        self._emit("call", call.name, str(len(call.args)), func.name)

        for stmt in func.body:
            callee._exec_stmt(stmt)

        self._temp_counter = callee._temp_counter

        return callee.scalars[func.name]


def run(program: Program) -> ExecutionResult:
    return Interpreter().execute(program)
