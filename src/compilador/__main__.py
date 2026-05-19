"""CLI: `python -m compilador <archivo>` — tokens (Fase 1) o `--parse` (Fase 2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lark import UnexpectedCharacters, UnexpectedInput

from compilador.errors import format_unexpected_characters, format_unexpected_input
from compilador.lexer import tokenize_file
from compilador.parser import parse_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compilador", description="Compilador por fases.")
    parser.add_argument("path", type=Path, help="Ruta a un archivo fuente (.txt)")
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Fase 2: árbol de parseo (sintaxis núcleo, sin if/while/for)",
    )
    args = parser.parse_args(argv)
    try:
        if args.parse:
            tree = parse_file(args.path)
            print(tree.pretty())
        else:
            tokens = tokenize_file(args.path)
            for t in tokens:
                line = getattr(t, "line", "?")
                col = getattr(t, "column", "?")
                print(f"{t.type}\t{t.value!r}\tL{line}C{col}")
    except UnexpectedCharacters as exc:
        sys.stderr.write(format_unexpected_characters(exc) + "\n")
        return 1
    except UnexpectedInput as exc:
        sys.stderr.write(format_unexpected_input(exc) + "\n")
        return 1
    except OSError as exc:
        sys.stderr.write(f"error: no se pudo leer {args.path}: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
