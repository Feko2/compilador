"""
Construcción del AST desde el parse tree de Lark.

Transforma bottom-up el árbol de parseo en nodos AST propios.
Soporta arreglos (array [N] of int, arr[i]) y funciones (function f(...) : int).
"""

from __future__ import annotations

from pathlib import Path

from lark import Token, Transformer

from compilador.ast_nodes import (
    AndCond,
    ArrayAccess,
    Assign,
    BinOp,
    Call,
    CallStmt,
    Comparison,
    Dec,
    Expr,
    ExprCond,
    For,
    FunctionDef,
    If,
    Inc,
    IntLit,
    LValue,
    NotCond,
    OrCond,
    Param,
    Program,
    Stmt,
    Var,
    VarDecl,
    While,
    Write,
)
from compilador.parser import parse as lark_parse

_OP_TOKENS = frozenset({
    "PLUS", "MINUS", "STAR", "SLASH", "PERCENT",
    "GT", "LT", "GE", "LE", "EQ", "NE",
})
_LOGIC_TOKENS = frozenset({"AND", "OR", "NOT"})
_PUNCT_TOKENS = frozenset({"LPAR", "RPAR", "LBRACE", "RBRACE", "LBRACK", "RBRACK", "COMMA", "SEMICOLON", "COLON"})


class ASTBuilder(Transformer):
    """Parse tree Lark → AST propio."""

    # --- Programa ------------------------------------------------------------

    def program(self, children):
        decls: list[VarDecl] = []
        functions: list[FunctionDef] = []
        body: list[Stmt] = []
        for item in children[3]:  # top_level_items transformado
            if isinstance(item, FunctionDef):
                functions.append(item)
            elif isinstance(item, list):
                if item and isinstance(item[0], VarDecl):
                    decls.extend(item)
                else:
                    body = item
        return Program(declarations=decls, functions=functions, body=body)

    def top_level_items(self, children):
        return list(children)

    def top_level_item(self, children):
        return children[0]

    def decls(self, children):
        return [decl for item in children if isinstance(item, list) for decl in item]

    def decl_item(self, children):
        declarators = children[0]  # lista de (nombre, tamaño|None)
        type_name, type_array_size = children[2]
        decls: list[VarDecl] = []
        for name, own_size in declarators:
            # Prioridad: tamaño inline del declarador (datos[6]) sobre el tipo.
            if own_size is not None:
                decls.append(VarDecl(name=name, type_name="int[]", array_size=own_size))
            elif type_array_size is not None:
                decls.append(VarDecl(name=name, type_name=type_name, array_size=type_array_size))
            else:
                decls.append(VarDecl(name=name, type_name=type_name, array_size=None))
        return decls

    def declarator_list(self, children):
        return [c for c in children if isinstance(c, tuple)]

    def scalar_declarator(self, children):
        return (children[0].value, None)

    def array_declarator(self, children):
        name = children[0].value
        size_tok = next(c for c in children if isinstance(c, Token) and c.type == "INTEGER")
        return (name, int(size_tok.value))

    def ident_list(self, children):
        return [tok.value for tok in children if isinstance(tok, Token) and tok.type == "IDENT"]

    def int_type(self, _children):
        return ("int", None)

    def array_type(self, children):
        size_tok = next(c for c in children if isinstance(c, Token) and c.type == "INTEGER")
        return ("int[]", int(size_tok.value))

    def function_def(self, children):
        name = next(c.value for c in children if isinstance(c, Token) and c.type == "IDENT")
        params: tuple[Param, ...] = ()
        body: list[Stmt] = []
        for child in children:
            if not isinstance(child, list):
                continue
            if child and isinstance(child[0], Param):
                params = tuple(child)
            elif isinstance(child[0], (Assign, CallStmt, Write, If, While, For, Inc, Dec)) if child else False:
                body = child
            elif not child:
                body = child
        return FunctionDef(name=name, params=params, return_type="int", body=body)

    def param_list(self, children):
        params: list[Param] = []
        for group in children:
            params.extend(group)
        return params

    def param_group(self, children):
        names = children[0]
        return [Param(name=name) for name in names]

    def stmt_section(self, children):
        return children[2]

    def stmt_list(self, children):
        return list(children)

    # --- Sentencias ----------------------------------------------------------

    def assign_stmt(self, children):
        return Assign(target=children[0], value=self._to_expr(children[2]))

    def var_lvalue(self, children):
        return children[0].value

    def array_lvalue(self, children):
        return ArrayAccess(name=children[0].value, index=self._to_expr(children[2]))

    def int_lvalue(self, children):
        return IntLit(value=int(children[0].value))

    def call_stmt(self, children):
        name = children[0].value
        args: tuple[Expr, ...] = ()
        for child in children[1:]:
            if isinstance(child, tuple):
                args = child
        return CallStmt(call=Call(name=name, args=args))

    def write_stmt(self, children):
        return Write(arg=children[2])

    def write_arg(self, children):
        val = children[0]
        if isinstance(val, Token) and val.type == "STRING":
            return val.value[1:-1]
        return self._to_expr(val)

    def if_stmt(self, children):
        else_body = children[6] if len(children) > 6 else []
        return If(condition=children[2], then_body=children[5], else_body=else_body)

    def else_clause(self, children):
        result = children[1]
        return result if isinstance(result, list) else [result]

    def while_stmt(self, children):
        return While(condition=children[2], body=children[5])

    def for_stmt(self, children):
        return For(init=children[2], condition=children[4], update=children[6], body=children[8])

    def for_init(self, children):
        return Assign(target=children[0].value, value=self._to_expr(children[2]))

    def for_inc(self, children):
        return Inc(target=children[0].value)

    def for_dec(self, children):
        return Dec(target=children[0].value)

    def for_assign(self, children):
        return Assign(target=children[0].value, value=self._to_expr(children[2]))

    def dec_stmt(self, children):
        return Dec(target=children[0].value)

    def inc_stmt(self, children):
        return Inc(target=children[0].value)

    def block(self, children):
        return children[1]

    # --- Condiciones ---------------------------------------------------------

    def and_(self, children):
        left, right = self._extract_cond_operands(children)
        return AndCond(left=left, right=right)

    def or_(self, children):
        left, right = self._extract_cond_operands(children)
        return OrCond(left=left, right=right)

    def not_(self, children):
        operand = next(
            c for c in children
            if not (isinstance(c, Token) and c.type in _LOGIC_TOKENS)
        )
        return NotCond(operand=operand)

    def paren_cond(self, children):
        return children[1]

    def cmp_gt(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op=">", left=left, right=right)

    def cmp_lt(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op="<", left=left, right=right)

    def cmp_ge(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op=">=", left=left, right=right)

    def cmp_le(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op="<=", left=left, right=right)

    def cmp_eq(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op="==", left=left, right=right)

    def cmp_ne(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op="!=", left=left, right=right)

    def expr_cond(self, children):
        return ExprCond(expr=self._to_expr(children[0]))

    # --- Expresiones ---------------------------------------------------------

    def add(self, children):
        left, right = self._extract_bin_operands(children)
        return BinOp(op="+", left=left, right=right)

    def sub(self, children):
        left, right = self._extract_bin_operands(children)
        return BinOp(op="-", left=left, right=right)

    def mul(self, children):
        left, right = self._extract_bin_operands(children)
        return BinOp(op="*", left=left, right=right)

    def div(self, children):
        left, right = self._extract_bin_operands(children)
        return BinOp(op="/", left=left, right=right)

    def mod(self, children):
        left, right = self._extract_bin_operands(children)
        return BinOp(op="%", left=left, right=right)

    def neg(self, children):
        operand = next(
            c for c in children
            if not (isinstance(c, Token) and c.type == "MINUS")
        )
        return BinOp(op="-", left=IntLit(value=0), right=self._to_expr(operand))

    def call(self, children):
        name = children[0].value
        args: tuple[Expr, ...] = ()
        for child in children[1:]:
            if isinstance(child, tuple):
                args = child
        return Call(name=name, args=args)

    def arg_list(self, children):
        return tuple(
            self._to_expr(c)
            for c in children
            if not (isinstance(c, Token) and c.type == "COMMA")
        )

    def var_ref(self, children):
        return Var(name=children[0].value)

    def array_ref(self, children):
        return ArrayAccess(name=children[0].value, index=self._to_expr(children[2]))

    def int_lit(self, children):
        tok = children[0]
        return IntLit(value=int(tok.value)) if isinstance(tok, Token) else tok

    def paren(self, children):
        inner = next(
            c for c in children
            if not (isinstance(c, Token) and c.type in {"LPAR", "RPAR"})
        )
        return self._to_expr(inner)

    def __default_token__(self, token):
        return token

    # --- Helpers -------------------------------------------------------------

    def _extract_cmp_operands(self, children):
        operands = [
            self._to_expr(c)
            for c in children
            if not (isinstance(c, Token) and c.type in _OP_TOKENS)
        ]
        return operands[0], operands[1]

    def _extract_cond_operands(self, children):
        operands = [
            c for c in children
            if not (isinstance(c, Token) and c.type in _LOGIC_TOKENS)
        ]
        return operands[0], operands[1]

    def _extract_bin_operands(self, children):
        operands = [
            self._to_expr(c)
            for c in children
            if not (isinstance(c, Token) and c.type in _OP_TOKENS)
        ]
        return operands[0], operands[1]

    def _to_expr(self, node) -> Expr:
        if isinstance(node, (Var, IntLit, BinOp, ArrayAccess, Call)):
            return node
        if isinstance(node, Token):
            if node.type == "IDENT":
                return Var(name=node.value)
            if node.type == "INTEGER":
                return IntLit(value=int(node.value))
        return node


def build_ast(text: str) -> Program:
    tree = lark_parse(text)
    return ASTBuilder().transform(tree)


def build_ast_from_file(path: Path) -> Program:
    return build_ast(path.read_text(encoding="utf-8"))
