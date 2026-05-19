"""Informes visuales HTML del compilador."""

from __future__ import annotations

from pathlib import Path

from compilador.viz.collect import build_report
from compilador.viz.html import render_html, write_report_html
from compilador.viz.models import CompilationReport, MemoryCell, Quadruple

__all__ = [
    "CompilationReport",
    "MemoryCell",
    "Quadruple",
    "build_report",
    "generate_report",
    "render_html",
    "write_report_html",
]


def generate_report(
    source: Path,
    output: Path | None = None,
    *,
    try_parse: bool = True,
) -> Path:
    """Genera `archivo.report.html` (o la ruta indicada) y devuelve su path."""
    report = build_report(source, try_parse=try_parse)
    dest = output or source.with_suffix(source.suffix + ".report.html")
    write_report_html(report, dest)
    return dest
