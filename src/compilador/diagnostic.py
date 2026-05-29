"""Diagnósticos estructurados para informes visuales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Phase = Literal["lex", "syntax", "semantic", "runtime"]


@dataclass(frozen=True)
class Diagnostic:
    phase: Phase
    line: int
    column: int
    message: str
    hint: str = ""

    @property
    def code(self) -> str:
        return f"{self.phase}:{self.line}:{self.column}"
