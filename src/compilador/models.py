"""
Modelos de datos compartidos entre módulos.

Contiene estructuras que usan tanto el intérprete como el visualizador,
evitando dependencias circulares.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Quadruple:
    """Cuádruplo de código intermedio: (índice, operador, arg1, arg2, resultado).
    
    Formato clásico de IR descrito en el Mod 3 del curso:
    cada instrucción tiene un operador y hasta dos operandos, más un destino.
    """
    index: int
    op: str
    arg1: str
    arg2: str
    result: str


@dataclass
class MemoryCell:
    """Celda de memoria: representa una variable en la tabla de símbolos en runtime."""
    name: str
    type_name: str
    value: str
