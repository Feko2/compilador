"""Recopila datos de las fases implementadas para el informe visual."""

from __future__ import annotations

from pathlib import Path

from lark import UnexpectedCharacters, UnexpectedInput

from compilador.errors import diagnostic_from_characters, diagnostic_from_input
from compilador.lexer import tokenize
from compilador.parser import parse
from compilador.viz.models import CompilationReport


def build_report(path: Path, *, try_parse: bool = True) -> CompilationReport:
    text = path.read_text(encoding="utf-8")
    report = CompilationReport(source_path=str(path), source_text=text)
    report.phases_available = {
        "lex": True,
        "parse": try_parse,
        "semantic": False,
        "ir": False,
        "runtime": False,
    }

    try:
        report.tokens = list(tokenize(text))
    except UnexpectedCharacters as exc:
        report.diagnostics.append(diagnostic_from_characters(exc))
        return report

    if not try_parse:
        return report

    try:
        tree = parse(text)
        report.parse_tree = tree.pretty()
    except UnexpectedInput as exc:
        report.diagnostics.append(diagnostic_from_input(exc))

    return report
