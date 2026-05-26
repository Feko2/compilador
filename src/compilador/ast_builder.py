"""
Fase 4 — Construcción del AST desde el parse tree de Lark.

Usa un Transformer de Lark para recorrer bottom-up el árbol de parseo
y construir nodos AST propios (definidos en ast_nodes.py).

Flujo: texto fuente → Lark parser → Tree → ASTBuilder → Program (AST)

Cada método transforma un nodo del parse tree (nombrado igual que la regla
en la gramática) en un nodo AST. Los métodos reciben los hijos ya
transformados.
"""

from __future__ import annotations

from pathlib import Path

from lark import Token, Transformer, Tree

from compilador.ast_nodes import (
    AndCond,
    Assign,
    BinOp,
    Cond,
    Comparison,
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
from compilador.parser import parse as lark_parse


class ASTBuilder(Transformer):
    """Transforma un parse tree Lark → nodos AST propios.
    
    Los nombres de métodos corresponden a las reglas en program.lark.
    Lark llama cada método con los hijos ya transformados (bottom-up).
    """

    # --- Programa ------------------------------------------------------------

    def program(self, children):
        # children: [PROGRAM, MAIN, LBRACE, decls, stmt_section, RBRACE]
        decls = children[3]       # resultado de self.decls()
        stmts = children[4]      # resultado de self.stmt_section()
        return Program(declarations=decls, body=stmts)

    def decls(self, children):
        # children: [VAR, ident_list, COLON, INT_KW, SEMICOLON]
        names = children[1]  # resultado de self.ident_list()
        return [VarDecl(name=n, type_name="int") for n in names]

    def ident_list(self, children):
        # children: [IDENT, COMMA?, IDENT, COMMA?, ...]
        return [tok.value for tok in children if isinstance(tok, Token) and tok.type == "IDENT"]

    def stmt_section(self, children):
        # children: [BEGIN, SEMICOLON, stmt_list, END, SEMICOLON]
        return children[2]  # la lista de sentencias

    def stmt_list(self, children):
        return list(children)

    # --- Sentencias ----------------------------------------------------------

    def assign_stmt(self, children):
        # children: [IDENT, ASSIGN, expr, SEMICOLON]
        target = children[0].value
        expr_val = self._to_expr(children[2])
        return Assign(target=target, value=expr_val)

    def write_stmt(self, children):
        # children: [WRITE, LPAR, write_arg, RPAR, SEMICOLON]
        return Write(arg=children[2])

    def write_arg(self, children):
        # children: [expr] o [STRING]
        val = children[0]
        if isinstance(val, Token) and val.type == "STRING":
            return val.value[1:-1]
        return self._to_expr(val)

    def if_stmt(self, children):
        # children: [IF, LPAR, condition, RPAR, THEN, block, else_clause?]
        cond = children[2]
        then_body = children[5]
        else_body = children[6] if len(children) > 6 else []
        return If(condition=cond, then_body=then_body, else_body=else_body)

    def else_clause(self, children):
        # children: [ELSE, block] o [ELSE, if_stmt]
        result = children[1]
        if isinstance(result, list):
            return result
        # Es un if_stmt embebido (else if)
        return [result]

    def while_stmt(self, children):
        # children: [WHILE, LPAR, condition, RPAR, DO, block]
        return While(condition=children[2], body=children[5])

    def for_stmt(self, children):
        # children: [FOR, LPAR, for_init, SEMICOLON, condition, SEMICOLON, for_update, RPAR, block]
        init = children[2]
        cond = children[4]
        update = children[6]
        body = children[8]
        return For(init=init, condition=cond, update=update, body=body)

    def for_init(self, children):
        # children: [IDENT, ASSIGN, expr]
        return Assign(target=children[0].value, value=self._to_expr(children[2]))

    def for_inc(self, children):
        # children: [IDENT, INC]
        return Inc(target=children[0].value)

    def for_dec(self, children):
        # children: [IDENT, DEC]
        return Dec(target=children[0].value)

    def for_assign(self, children):
        # children: [IDENT, ASSIGN, expr]
        return Assign(target=children[0].value, value=self._to_expr(children[2]))

    def dec_stmt(self, children):
        # children: [IDENT, DEC, SEMICOLON]
        return Dec(target=children[0].value)

    def inc_stmt(self, children):
        # children: [IDENT, INC, SEMICOLON]
        return Inc(target=children[0].value)

    def block(self, children):
        # children: [LBRACE, stmt_list, RBRACE]
        return children[1]

    # --- Condiciones ---------------------------------------------------------

    def condition(self, children):
        # children: [cond_atom, AND?, cond_atom, AND?, ...]
        # Filtra tokens AND, queda solo los cond_atoms
        atoms = [c for c in children if not isinstance(c, Token)]
        result = atoms[0]
        for atom in atoms[1:]:
            result = AndCond(left=result, right=atom)
        return result

    def paren_cond(self, children):
        # children: [LPAR, condition, RPAR]
        return children[1]

    def cmp_gt(self, children):
        # children: [expr, GT, expr]
        left, right = self._extract_cmp_operands(children)
        return Comparison(op=">", left=left, right=right)

    def cmp_lt(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op="<", left=left, right=right)

    def cmp_ge(self, children):
        left, right = self._extract_cmp_operands(children)
        return Comparison(op=">=", left=left, right=right)

    def _extract_cmp_operands(self, children):
        """Extrae los dos operandos de una comparación, ignorando el token operador."""
        # Los hijos son [expr_o_token, OP_TOKEN, expr_o_token]
        # pero expr puede ser un Token si es un IDENT/INTEGER simple
        ops = {"GT", "LT", "GE"}
        operands = [self._to_expr(c) for c in children if not (isinstance(c, Token) and c.type in ops)]
        return operands[0], operands[1]

    def _to_expr(self, node) -> Expr:
        """Convierte un nodo (Token o ya transformado) a un nodo Expr."""
        if isinstance(node, (Var, IntLit, BinOp)):
            return node
        if isinstance(node, Token):
            if node.type == "IDENT":
                return Var(name=node.value)
            if node.type == "INTEGER":
                return IntLit(value=int(node.value))
        return node

    def expr_cond(self, children):
        # children: [expr] — una expresión usada como condición (potencial error semántico)
        return ExprCond(expr=self._to_expr(children[0]))

    # --- Expresiones aritméticas ---------------------------------------------

    def add(self, children):
        ops = {"PLUS", "MINUS", "STAR"}
        operands = [self._to_expr(c) for c in children if not (isinstance(c, Token) and c.type in ops)]
        return BinOp(op="+", left=operands[0], right=operands[1])

    def sub(self, children):
        ops = {"PLUS", "MINUS", "STAR"}
        operands = [self._to_expr(c) for c in children if not (isinstance(c, Token) and c.type in ops)]
        return BinOp(op="-", left=operands[0], right=operands[1])

    def mul(self, children):
        ops = {"PLUS", "MINUS", "STAR"}
        operands = [self._to_expr(c) for c in children if not (isinstance(c, Token) and c.type in ops)]
        return BinOp(op="*", left=operands[0], right=operands[1])

    def factor(self, children):
        # factor: IDENT | INTEGER | LPAR expr RPAR
        # Filtra paréntesis
        non_paren = [c for c in children if not (isinstance(c, Token) and c.type in ("LPAR", "RPAR"))]
        if len(non_paren) == 1:
            return self._to_expr(non_paren[0])
        return self._to_expr(non_paren[0])

    def __default_token__(self, token):
        """Tokens no transformados se pasan tal cual (los consumimos en los métodos padres)."""
        return token


# =============================================================================
# API PÚBLICA
# =============================================================================

def build_ast(text: str) -> Program:
    """Parsea el texto fuente y construye el AST completo."""
    tree = lark_parse(text)
    return ASTBuilder().transform(tree)


def build_ast_from_file(path: Path) -> Program:
    """Lee un archivo fuente y devuelve su AST."""
    return build_ast(path.read_text(encoding="utf-8"))
