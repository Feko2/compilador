"""Genera un informe HTML con código coloreado, errores y paneles por fase."""

from __future__ import annotations

import html
from pathlib import Path

from lark import Token

from compilador.diagnostic import Diagnostic
from compilador.models import MemoryCell, Quadruple
from compilador.viz.models import CompilationReport
from compilador.viz.token_style import css_class_for_token

_CSS = """
:root {
  --bg: #05070a;
  --crt: #0a0f0c;
  --panel: #0b110d;
  --green: #3bff84;
  --green-dim: #1f9d52;
  --text: #c8f7d8;
  --muted: #5f7d6b;
  --line: #14361f;
  --amber: #ffcc4d;
  --cyan: #56d4ff;
  --err-bg: #1c0f10;
  --err-border: #ff5f56;
}
* { box-sizing: border-box; }
html { background: var(--bg); }
body {
  font-family: "SF Mono", "JetBrains Mono", Menlo, Consolas, "DejaVu Sans Mono", monospace;
  background:
    radial-gradient(ellipse at 50% 0%, #0c1611 0%, var(--bg) 70%);
  color: var(--text);
  margin: 0;
  padding: 2rem 1.25rem;
  line-height: 1.5;
  font-size: 14px;
  min-height: 100vh;
}
/* CRT scanlines + flicker overlay */
body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.18) 0px,
    rgba(0, 0, 0, 0.18) 1px,
    transparent 2px,
    transparent 3px
  );
  mix-blend-mode: multiply;
  z-index: 9999;
  animation: flicker 4s infinite steps(60);
}
@keyframes flicker {
  0%, 96%, 100% { opacity: 1; }
  97% { opacity: 0.82; }
  98% { opacity: 0.96; }
}
/* Terminal window */
.term {
  max-width: 1080px;
  margin: 0 auto;
  background: var(--crt);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow:
    0 0 0 1px rgba(59, 255, 132, 0.06),
    0 24px 60px rgba(0, 0, 0, 0.7),
    0 0 80px rgba(31, 157, 82, 0.08);
  overflow: hidden;
}
.term-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: linear-gradient(#10160f, #0a0e0a);
  border-bottom: 1px solid var(--line);
}
.dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.dot-r { background: #ff5f56; }
.dot-y { background: #ffbd2e; }
.dot-g { background: #27c93f; }
.term-title {
  margin-left: 0.6rem;
  color: var(--muted);
  font-size: 0.8rem;
  letter-spacing: 0.02em;
}
.term-body { padding: 1.4rem 1.6rem 2rem; }
/* Boot banner */
.banner {
  color: var(--green);
  text-shadow: 0 0 8px rgba(59, 255, 132, 0.45);
  white-space: pre;
  font-size: 0.82rem;
  line-height: 1.2;
  margin: 0 0 0.75rem;
}
h1 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
  color: var(--green);
  text-shadow: 0 0 6px rgba(59, 255, 132, 0.4);
}
.meta { color: var(--muted); font-size: 0.82rem; margin: 0 0 1.5rem; }
.meta .ok { color: var(--green); }
.meta .bad { color: var(--err-border); }
.meta::before { content: "$ "; color: var(--green-dim); }
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  margin-bottom: 1rem;
  padding: 0.5rem 1.1rem 1.1rem;
}
section h2 {
  font-size: 0.86rem;
  margin: 0 0 0.85rem;
  padding: 0.45rem 0 0.5rem;
  color: var(--green);
  border-bottom: 1px dashed var(--line);
  letter-spacing: 0.02em;
  font-weight: 600;
}
section h2::before {
  content: "user@compilador:~$ ";
  color: var(--green-dim);
  font-weight: 400;
}
/* Bracketed status badges */
.badge {
  display: inline-block;
  font-size: 0.72rem;
  margin-left: 0.5rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.badge-ok { color: var(--green); }
.badge-warn { color: var(--err-border); }
.badge-pending { color: var(--muted); }
.source-wrap { overflow-x: auto; }
.source {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.82rem;
}
.source td { vertical-align: top; padding: 0 0.35rem; }
.source .ln {
  color: var(--green-dim);
  text-align: right;
  user-select: none;
  width: 2.5rem;
  padding-right: 0.75rem;
  opacity: 0.7;
}
.source .code { white-space: pre; }
.source tr.error-line { background: var(--err-bg); }
.source tr.error-line .ln { color: var(--err-border); font-weight: bold; opacity: 1; }
.err-marker { color: var(--err-border); font-size: 0.78rem; }
.diag {
  border-left: 3px solid var(--err-border);
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
  background: var(--err-bg);
}
.diag strong { color: var(--err-border); }
.diag .hint { color: var(--muted); margin-top: 0.35rem; font-size: 0.8rem; }
.diag .hint::before { content: "↳ "; }
.tok-keyword { color: #ff7b72; font-weight: 600; }
.tok-operator { color: #d2a8ff; }
.tok-punct { color: var(--muted); }
.tok-ident { color: var(--cyan); }
.tok-integer { color: var(--amber); }
.tok-string { color: var(--green); }
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
table.data th {
  color: var(--green);
  font-weight: 600;
  background: rgba(31, 157, 82, 0.06);
}
table.data tr:hover td { background: rgba(59, 255, 132, 0.04); }
pre.tree {
  margin: 0;
  font-size: 0.78rem;
  overflow-x: auto;
  white-space: pre;
  color: var(--text);
}
/* Program output as a console pane */
ul.console {
  list-style: none;
  margin: 0;
  padding: 0.75rem 0.9rem;
  background: #04060a;
  border: 1px solid var(--line);
  border-radius: 4px;
}
ul.console li { white-space: pre-wrap; }
ul.console li::before { content: "» "; color: var(--green-dim); }
.empty { color: var(--muted); font-style: italic; font-size: 0.85rem; }
.empty::before { content: "// "; }
.legend { font-size: 0.75rem; color: var(--muted); margin-top: 0.6rem; }
.legend span { margin-right: 0.75rem; }
.cursor {
  display: inline-block;
  width: 0.55em;
  height: 1em;
  background: var(--green);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1.1s steps(2, start) infinite;
  box-shadow: 0 0 6px rgba(59, 255, 132, 0.6);
}
@keyframes blink { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }
"""

_PENDING = (
    '<p class="empty">Pendiente en una fase posterior del compilador. '
    "El informe mostrará datos aquí cuando esté implementado.</p>"
)

# Fases que, si fallan, impiden llegar a la ejecución (IR / memoria / salida).
_PRE_RUNTIME_PHASES = frozenset({"lex", "syntax", "semantic"})


def _runtime_empty_reason(report: CompilationReport) -> str:
    """Explica por qué una sección de runtime (IR/memoria/salida) está vacía."""
    if not report.phases_available.get("parse", True):
        return (
            '<p class="empty">Parser desactivado (--no-parse): no se ejecutó '
            "la generación de cuádruplos ni el runtime.</p>"
        )
    blocking = [d for d in report.diagnostics if d.phase in _PRE_RUNTIME_PHASES]
    if blocking:
        phase = blocking[0].phase
        return (
            f'<p class="empty">No se generó: la compilación se detuvo por un error '
            f"de tipo <strong>{_escape(phase)}</strong> antes de la ejecución. "
            "Corrige los errores de la sección superior para ver esta fase.</p>"
        )
    return (
        '<p class="empty">Sin datos: el programa no produjo resultados en esta fase.</p>'
    )


def _escape(s: str) -> str:
    return html.escape(s, quote=True)


def _badge(ok: bool | None) -> str:
    if ok is True:
        return '<span class="badge badge-ok">[  OK  ]</span>'
    if ok is False:
        return '<span class="badge badge-warn">[ FAIL ]</span>'
    return '<span class="badge badge-pending">[ ---- ]</span>'


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


def _render_quadruples(report: CompilationReport) -> str:
    quads = report.quadruples
    if not quads:
        return _runtime_empty_reason(report)
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


def _render_memory(report: CompilationReport) -> str:
    cells = report.memory
    if not cells:
        return _runtime_empty_reason(report)
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


def _render_output(report: CompilationReport) -> str:
    lines = report.program_output
    if not lines:
        return _runtime_empty_reason(report)
    body = "".join(f"<li>{_escape(line)}</li>" for line in lines)
    return f'<ul class="console">{body}</ul>'


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

    name = _escape(Path(report.source_path).name)
    status_html = (
        '<span class="ok">OK</span>'
        if report.ok
        else '<span class="bad">CON ERRORES</span>'
    )
    n_tokens = len(report.tokens)
    n_diag = len(report.diagnostics)
    banner = _escape(
        r"""   ___                _ _           _
  / __\___  _ __ ___ | (_) | __ _  __| | ___  _ __
 / /  / _ \| '_ ` _ \| | | |/ _` |/ _` |/ _ \| '__|
/ /__| (_) | | | | | | | | | (_| | (_| | (_) | |
\____/\___/|_| |_| |_|_|_|_|\__,_|\__,_|\___/|_|"""
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Informe — {name}</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="term">
    <div class="term-bar">
      <span class="dot dot-r"></span>
      <span class="dot dot-y"></span>
      <span class="dot dot-g"></span>
      <span class="term-title">compilador — report — {name}</span>
    </div>
    <div class="term-body">
      <pre class="banner">{banner}</pre>
      <h1>Informe de compilación</h1>
      <p class="meta">compilar {_escape(report.source_path)} \u2014 estado: {status_html} \u2014 \
{n_tokens} tokens, {n_diag} diagnóstico(s)<span class="cursor"></span></p>

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
        {_render_quadruples(report)}
      </section>

      <section>
        <h2>Memoria (tabla de símbolos / runtime) {_badge(None if not report.memory else True)}</h2>
        {_render_memory(report)}
      </section>

      <section>
        <h2>Salida del programa (write) {_badge(None if not report.program_output else True)}</h2>
        {_render_output(report)}
      </section>
    </div>
  </div>
</body>
</html>"""


def write_report_html(report: CompilationReport, output: Path) -> Path:
    output.write_text(render_html(report), encoding="utf-8")
    return output
