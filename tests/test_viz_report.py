"""Informe HTML visual — tests de integración."""

from __future__ import annotations

from pathlib import Path

from compilador.viz import build_report, generate_report, render_html

ROOT = Path(__file__).resolve().parents[1]
PRUEBAS = ROOT / "pruebas"

NUCLEO_FOR = """\
program main{
\tvar i,n,x : int;
\tbegin;
\t\twrite("factorial for");
\t\tx:=1;
\tend;
}"""


def test_render_html_has_sections() -> None:
    report = build_report(PRUEBAS / "pruebaIf.txt")
    html = render_html(report)
    assert "Cuádruplos" in html
    assert "Memoria" in html
    assert "Salida del programa" in html
    assert "tok-keyword" in html


def test_report_prueba_if_parses_ok() -> None:
    """Con la gramática Fase 3, pruebaIf.txt parsea sin error sintáctico."""
    report = build_report(PRUEBAS / "pruebaIf.txt")
    assert not any(d.phase == "syntax" for d in report.diagnostics)
    assert report.parse_tree is not None


def test_report_nucleo_parses(tmp_path: Path) -> None:
    src = tmp_path / "mini.txt"
    src.write_text(NUCLEO_FOR, encoding="utf-8")
    report = build_report(src)
    assert report.parse_tree is not None
    assert not any(d.phase == "syntax" for d in report.diagnostics)


def test_generate_report_writes_file(tmp_path: Path) -> None:
    src = tmp_path / "mini.txt"
    src.write_text(NUCLEO_FOR, encoding="utf-8")
    out = generate_report(src)
    assert out.exists()
    assert out.suffix == ".html"
    assert "Informe de compilación" in out.read_text(encoding="utf-8")
