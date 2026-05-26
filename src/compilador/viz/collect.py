"""
Recopila datos de TODAS las fases implementadas para el informe visual.

Pipeline: texto → léxico → parser → AST → semántica → ejecución
Cada fase se intenta en orden; si una falla, se registra el diagnóstico
y se detiene (las fases posteriores no se ejecutan).
"""

from __future__ import annotations

from pathlib import Path

from lark import UnexpectedCharacters, UnexpectedInput

from compilador.ast_builder import build_ast
from compilador.errors import diagnostic_from_characters, diagnostic_from_input
from compilador.interpreter import run
from compilador.lexer import tokenize
from compilador.parser import parse
from compilador.semantic import analyze
from compilador.viz.models import CompilationReport
from compilador.models import MemoryCell


def build_report(path: Path, *, try_parse: bool = True) -> CompilationReport:
    """Construye un informe ejecutando todas las fases disponibles."""
    text = path.read_text(encoding="utf-8")
    report = CompilationReport(source_path=str(path), source_text=text)
    report.phases_available = {
        "lex": True,
        "parse": try_parse,
        "semantic": try_parse,
        "ir": try_parse,
        "runtime": try_parse,
    }

    # Fase 1: Léxico
    try:
        report.tokens = list(tokenize(text))
    except UnexpectedCharacters as exc:
        report.diagnostics.append(diagnostic_from_characters(exc))
        return report

    if not try_parse:
        return report

    # Fase 2-3: Parser
    try:
        tree = parse(text)
        report.parse_tree = tree.pretty()
    except UnexpectedInput as exc:
        report.diagnostics.append(diagnostic_from_input(exc))
        return report

    # Fase 4: AST
    try:
        ast = build_ast(text)
    except Exception as exc:
        from compilador.diagnostic import Diagnostic
        report.diagnostics.append(Diagnostic(
            phase="syntax",
            line=1,
            column=1,
            message=f"Error construyendo AST: {exc}",
            hint="Posible error interno en la transformación del parse tree.",
        ))
        return report

    # Fase 5: Semántica
    table, sem_errors = analyze(ast)
    if sem_errors:
        report.diagnostics.extend(sem_errors)
        # Aún intentamos generar memoria desde la tabla de símbolos
        report.memory = [
            MemoryCell(name=s.name, type_name=s.type_name, value="?")
            for s in table.symbols.values()
        ]
        return report

    # Fase 6-7: Ejecución
    result = run(ast)
    report.quadruples = result.quadruples
    report.memory = [
        MemoryCell(name=name, type_name="int", value=str(val))
        for name, val in result.memory.items()
    ]
    report.program_output = result.output
    if result.errors:
        report.diagnostics.extend(result.errors)

    return report
