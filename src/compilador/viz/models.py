"""Modelos del informe de compilación (crece con cada fase)."""

from __future__ import annotations

from dataclasses import dataclass, field

from lark import Token

from compilador.diagnostic import Diagnostic
from compilador.models import MemoryCell, Quadruple  # noqa: F401 — re-export


@dataclass
class CompilationReport:
    """Resultado completo de todas las fases, para visualizar en HTML."""
    source_path: str
    source_text: str
    tokens: list[Token] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    parse_tree: str | None = None
    quadruples: list[Quadruple] = field(default_factory=list)
    memory: list[MemoryCell] = field(default_factory=list)
    program_output: list[str] = field(default_factory=list)
    phases_available: dict[str, bool] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.diagnostics
