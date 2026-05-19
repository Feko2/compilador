"""Genera un informe HTML con código coloreado, errores y paneles por fase."""

from __future__ import annotations

import html
from pathlib import Path

from lark import Token

from compilador.diagnostic import Diagnostic
from compilador.viz.models import CompilationReport, MemoryCell, Quadruple
from compilador.viz.token_style import css_class_for_token

_CSS = """
:root {
  --bg: #0f1419;
  --panel: #1a2332;
  --text: #e6edf3;
  --muted: #8b949e;
  --line: #30363d;
  --err-bg: #3d1f24;
  --err-border: #f85149;
}
* { box-sizing: border-box; }
body {
  font-family: "SF Mono", Menlo, Consolas, monospace;
  background: var(--bg);
  color: var(--text);
  margin: 0;
  padding: 1.5rem;
  line-height: 1.45;
}
h1 { font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }
.meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 1.5rem; }
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
}
section h2 {
  font-size: 0.95rem;
  margin: 0 0 0.75rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  vertical-align: middle;
}
.badge-ok { background: #238636; color: #fff; }
.badge-warn { background: #9e6a03; color: #fff; }
.badge-pending { background: #30363d; color: var(--muted); }
.source-wrap { overflow-x: auto; }
.source {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.82rem;
}
.source td { vertical-align: top; padding: 0 0.35rem; }
.source .ln {
  color: var(--muted);
  text-align: right;
  user-select: none;
  width: 2.5rem;
  padding-right: 0.75rem;
}
.source .code { white-space: pre; }
.source tr.error-line { background: var(--err-bg); }
.source tr.error-line .ln { color: var(--err-border); font-weight: bold; }
.err-marker { color: var(--err-border); font-size: 0.75rem; }
.diag {
  border-left: 3px solid var(--err-border);
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
  background: var(--err-bg);
}
.diag strong { color: var(--err-border); }
.diag .hint { color: var(--muted); margin-top: 0.35rem; font-size: 0.8rem; }
.tok-keyword { color: #ff7b72; }
.tok-operator { color: #d2a8ff; }
.tok-punct { color: #8b949e; }
.tok-ident { color: #79c0ff; }
.tok-integer { color: #a5d6ff; }
.tok-string { color: #7ee787; }
.tok-other { color: #ffa657; }
table.data {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
table.data th, table.data td {
  border: 1px solid var(--line);
  padding: 0.35rem 0.5rem;
  text-align: left;
}
table.data th { color: var(--muted); font-weight: 500; }
pre.tree {
  margin: 0;
  font-size: 0.78rem;
  overflow-x: auto;
  white-space: pre;
}
.empty { color: var(--muted); font-style: italic; font-size: 0.85rem; }
.legend { font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; }
.legend span { margin-right: 0.75rem; }
"""

_PENDING = (
    '<p class="empty">Pendiente en una fase posterior del compilador. '
    "El informe mostrará datos aquí cuando esté implementado.</p>"
)


def _escape(s: str) -> str:
    return html.escape(s, quote=True)


def _badge(ok: bool | None) -> str:
    if ok is True:
        return '<span class="badge badge-ok">OK</span>'
    if ok is False:
        return '<span class="badge badge-warn">error</span>'
    return '<span class="badge badge-pending">pendiente</span>'


def _tokens_by_line(tokens: list[Token]) -> dict[int, list[Token]]:
    by_line: dict[int, list[Token]] = {}
    for t in tokens:
        line = getattr(t, "line", None)
        if line is None:
            continue
        by_line.setdefault(int(line), []).append(t)
    for line_tokens in by_line.values():
        line_tokens.sort(key=lambda t: int(getattr(t, "column", 0) or 0))
    return by_line


def _diagnostics_by_line(diagnostics: list[Diagnostic]) -> dict[int, list[Diagnostic]]:
    by_line: dict[int, list[Diagnostic]] = {}
    for d in diagnostics:
        by_line.setdefault(d.line, []).append(d)
    return by_line


def _highlight_line(line: str, tokens: list[Token]) -> str:
    if not tokens:
        return _escape(line) if line else "&nbsp;"

    markers: list[tuple[int, int, str, str]] = []
    for t in tokens:
        col = int(getattr(t, "column", 1) or 1)
        start = col - 1
        end = start + len(str(t.value))
        markers.append((start, end, css_class_for_token(t.type), f"{t.type} {t.value!r}"))

    markers.sort(key=lambda m: m[0])
    parts: list[str] = []
    pos = 0
    for start, end, css, title in markers:
        start = max(0, min(start, len(line)))
        end = max(start, min(end, len(line)))
        if start > pos:
            parts.append(_escape(line[pos:start]))
        if end > start:
            parts.append(
                f'<span class="{css}" title="{_escape(title)}">{_escape(line[start:end])}</span>'
            )
        pos = max(pos, end)
    if pos < len(line):
        parts.append(_escape(line[pos:]))
    return "".join(parts) if parts else "&nbsp;"


def _render_source(report: CompilationReport) -> str:
    lines = report.source_text.splitlines()
    tokens_by_line = _tokens_by_line(report.tokens)
    diags_by_line = _diagnostics_by_line(report.diagnostics)
    rows: list[str] = []

    for i, line in enumerate(lines, start=1):
        err_class = ' class="error-line"' if i in diags_by_line else ""
        highlighted = _highlight_line(line, tokens_by_line.get(i, []))
        rows.append(
            f'<tr{err_class}><td class="ln">{i}</td><td class="code">{highlighted}</td></tr>'
        )
        for d in diags_by_line.get(i, []):
            col = max(1, d.column)
            pad = "&nbsp;" * (col - 1)
            rows.append(
                f'<tr class="error-line"><td></td><td class="err-marker">'
                f"{pad}^ {_escape(d.phase.upper())}</td></tr>"
            )

    if not lines:
        rows.append('<tr><td class="ln">1</td><td class="code">&nbsp;</td></tr>')

    legend = (
        '<p class="legend">'
        '<span class="tok-keyword">palabra clave</span> '
        '<span class="tok-ident">identificador</span> '
        '<span class="tok-integer">entero</span> '
        '<span class="tok-string">cadena</span> '
        '<span class="tok-operator">operador</span>'
        "</p>"
    )
    return (
        f'<div class="source-wrap"><table class="source"><tbody>{"".join(rows)}'
        f"</tbody></table>{legend}</div>"
    )


def _render_diagnostics(report: CompilationReport) -> str:
    if not report.diagnostics:
        return '<p class="empty">Sin errores en las fases ejecutadas.</p>'
    parts = []
    for d in report.diagnostics:
        hint = f'<div class="hint">{_escape(d.hint)}</div>' if d.hint else ""
        parts.append(
            f'<div class="diag"><strong>[{d.phase}]</strong> {_escape(d.message)}{hint}</div>'
        )
    return "".join(parts)


def _render_tokens_table(report: CompilationReport) -> str:
    if not report.tokens:
        return '<p class="empty">Sin tokens (error léxico previo).</p>'
    rows = []
    for t in report.tokens:
        line = getattr(t, "line", "?")
        col = getattr(t, "column", "?")
        css = css_class_for_token(t.type)
        rows.append(
            f"<tr><td class=\"{css}\">{_escape(t.type)}</td>"
            f"<td>{_escape(str(t.value))}</td><td>{line}</td><td>{col}</td></tr>"
        )
    return (
        "<table class=\"data\"><thead><tr><th>Tipo</th><th>Valor</th>"
        f"<th>Línea</th><th>Col</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _render_quadruples(quads: list[Quadruple]) -> str:
    if not quads:
        return _PENDING
    rows = []
    for q in quads:
        rows.append(
            f"<tr><td>{q.index}</td><td>{_escape(q.op)}</td>"
            f"<td>{_escape(q.arg1)}</td><td>{_escape(q.arg2)}</td>"
            f"<td>{_escape(q.result)}</td></tr>"
        )
    return (
        "<table class=\"data\"><thead><tr><th>#</th><th>Op</th><th>Arg1</th>"
        f"<th>Arg2</th><th>Result</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _render_memory(cells: list[MemoryCell]) -> str:
    if not cells:
        return _PENDING
    rows = []
    for c in cells:
        rows.append(
            f"<tr><td>{_escape(c.name)}</td><td>{_escape(c.type_name)}</td>"
            f"<td>{_escape(c.value)}</td></tr>"
        )
    return (
        "<table class=\"data\"><thead><tr><th>Variable</th><th>Tipo</th><th>Valor</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _render_output(lines: list[str]) -> str:
    if not lines:
        return _PENDING
    body = "".join(f"<li>{_escape(line)}</li>" for line in lines)
    return f"<ul>{body}</ul>"


def render_html(report: CompilationReport) -> str:
    lex_ok = bool(report.tokens) and not any(d.phase == "lex" for d in report.diagnostics)
    parse_ok = report.parse_tree is not None and not any(
        d.phase == "syntax" for d in report.diagnostics
    )

    parse_section = (
        f"<pre class=\"tree\">{_escape(report.parse_tree)}</pre>"
        if report.parse_tree
        else '<p class="empty">No hay árbol (error de sintaxis o parse desactivado).</p>'
    )

    status = "OK" if report.ok else "con errores"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>Informe — {_escape(Path(report.source_path).name)}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>Informe de compilación</h1>
  <p class="meta">{_escape(report.source_path)} · estado: <strong>{status}</strong></p>

  <section>
    <h2>Errores {_badge(False if report.diagnostics else True)}</h2>
    {_render_diagnostics(report)}
  </section>

  <section>
    <h2>Código fuente (tokens coloreados) {_badge(lex_ok)}</h2>
    {_render_source(report)}
  </section>

  <section>
    <h2>Tokens {_badge(lex_ok)}</h2>
    {_render_tokens_table(report)}
  </section>

  <section>
    <h2>Árbol de parseo {_badge(parse_ok if report.phases_available.get("parse") else None)}</h2>
    {parse_section}
  </section>

  <section>
    <h2>Cuádruplos (IR) {_badge(None if not report.quadruples else True)}</h2>
    {_render_quadruples(report.quadruples)}
  </section>

  <section>
    <h2>Memoria (tabla de símbolos / runtime) {_badge(None if not report.memory else True)}</h2>
    {_render_memory(report.memory)}
  </section>

  <section>
    <h2>Salida del programa (write) {_badge(None if not report.program_output else True)}</h2>
    {_render_output(report.program_output)}
  </section>
</body>
</html>"""


def write_report_html(report: CompilationReport, output: Path) -> Path:
    output.write_text(render_html(report), encoding="utf-8")
    return output
