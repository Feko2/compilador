"""CLI: `python -m compilador <archivo>` imprime tokens (Fase 1)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lark import UnexpectedCharacters

from compilador.errors import format_unexpected_characters
from compilador.lexer import tokenize_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compilador", description="Fase 1: volcado léxico.")
    parser.add_argument("path", type=Path, help="Ruta a un archivo fuente (.txt)")
    args = parser.parse_args(argv)
    try:
        tokens = tokenize_file(args.path)
    except UnexpectedCharacters as exc:
        sys.stderr.write(format_unexpected_characters(exc) + "\n")
        return 1
    except OSError as exc:
        sys.stderr.write(f"error: no se pudo leer {args.path}: {exc}\n")
        return 1
    for t in tokens:
        line = getattr(t, "line", "?")
        col = getattr(t, "column", "?")
        print(f"{t.type}\t{t.value!r}\tL{line}C{col}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
