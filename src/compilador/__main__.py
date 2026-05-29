"""
CLI del compilador — interfaz de línea de comandos.

Modos de uso:
    compilador archivo.txt             → muestra tokens (Fase 1)
    compilador archivo.txt --parse     → muestra árbol de parseo (Fase 2-3)
    compilador archivo.txt --run       → ejecuta el programa (Fases 4-7)
    compilador archivo.txt --report    → genera informe HTML completo
    compilador archivo.txt --check     → solo análisis semántico (Fase 5)

El pipeline completo es:
    texto → léxico → parser → AST → semántica → ejecución → salida
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lark import UnexpectedCharacters, UnexpectedInput

from compilador.errors import format_unexpected_characters, format_unexpected_input
from compilador.lexer import tokenize_file
from compilador.parser import parse_file
from compilador.ast_builder import build_ast_from_file
from compilador.semantic import analyze
from compilador.interpreter import run
from compilador.viz import generate_report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="compilador",
        description="Compilador por fases: léxico → sintaxis → AST → semántica → ejecución.",
    )
    ap.add_argument("path", type=Path, help="Ruta a un archivo fuente (.txt)")
    ap.add_argument(
        "--parse",
        action="store_true",
        help="Muestra el árbol de parseo (Fases 2-3)",
    )
    ap.add_argument(
        "--run",
        action="store_true",
        help="Ejecuta el programa completo (Fases 4-7): muestra la salida de write()",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="Solo análisis semántico (Fase 5): reporta errores de tipos",
    )
    ap.add_argument(
        "--report",
        nargs="?",
        const="",
        metavar="HTML",
        help="Genera informe HTML completo con todas las fases",
    )
    ap.add_argument(
        "--no-parse",
        action="store_true",
        help="Con --report: solo léxico (no intentar parsear)",
    )
    args = ap.parse_args(argv)

    # --- Modo informe HTML ---------------------------------------------------
    if args.report is not None:
        out = Path(args.report) if args.report else None
        try:
            dest = generate_report(args.path, out, try_parse=not args.no_parse)
        except OSError as exc:
            sys.stderr.write(f"error: no se pudo leer o escribir: {exc}\n")
            return 1
        print(dest)
        return 0

    # --- Modo ejecución (pipeline completo) ----------------------------------
    if args.run:
        try:
            ast = build_ast_from_file(args.path)
        except UnexpectedCharacters as exc:
            sys.stderr.write(format_unexpected_characters(exc) + "\n")
            return 1
        except UnexpectedInput as exc:
            sys.stderr.write(format_unexpected_input(exc) + "\n")
            return 1
        except OSError as exc:
            sys.stderr.write(f"error: no se pudo leer {args.path}: {exc}\n")
            return 1

        table, sem_errors = analyze(ast)
        if sem_errors:
            for err in sem_errors:
                sys.stderr.write(f"{err.message}\n")
                if err.hint:
                    sys.stderr.write(f"  hint: {err.hint}\n")
            return 1

        result = run(ast)
        for line in result.output:
            print(line)
        if result.errors:
            for err in result.errors:
                sys.stderr.write(f"{err.message}\n")
            return 1
        return 0

    # --- Modo chequeo semántico ----------------------------------------------
    if args.check:
        try:
            ast = build_ast_from_file(args.path)
        except UnexpectedCharacters as exc:
            sys.stderr.write(format_unexpected_characters(exc) + "\n")
            return 1
        except UnexpectedInput as exc:
            sys.stderr.write(format_unexpected_input(exc) + "\n")
            return 1
        except OSError as exc:
            sys.stderr.write(f"error: no se pudo leer {args.path}: {exc}\n")
            return 1

        table, sem_errors = analyze(ast)
        if sem_errors:
            for err in sem_errors:
                sys.stderr.write(f"{err.message}\n")
                if err.hint:
                    sys.stderr.write(f"  hint: {err.hint}\n")
            return 1
        print("OK: sin errores semánticos.")
        print(f"Variables declaradas: {', '.join(table.symbols.keys())}")
        return 0

    # --- Modo tokens (default) o parse ---------------------------------------
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
