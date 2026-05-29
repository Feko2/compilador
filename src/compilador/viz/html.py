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
  --bg: #ffffff;
  --page: #ececec;
  --titlebar-top: #e8e8e8;
  --titlebar-bottom: #d4d4d4;
  --titlebar-border: #b6b6b6;
  --text: #1d1d1f;
  --muted: #8a8a8e;
  --faint: #c7c7cc;
  --line: #e6e6e8;
  --line-strong: #d8d8da;
  --panel-alt: #f6f6f7;
  --prompt: #1a7f37;
  --blue: #2a5db0;
  --err: #c0392b;
  --err-bg: #fdecea;
  --err-line: #f4cfca;
  /* Syntax: muted, tasteful (no neon) */
  --kw: #9c3fb4;
  --str: #b5402f;
  --num: #2a5db0;
  --op: #6f6f73;
  --punct: #b0b0b3;
  --ident: #1d1d1f;
  --other: #8a6d3b;
}
* { box-sizing: border-box; }
html { background: var(--page); }
body {
  font-family: "SF Mono", "SFMono-Regular", ui-monospace, Menlo, Monaco, "Cascadia Code", Consolas, monospace;
  background: var(--page);
  color: var(--text);
  margin: 0;
  padding: 2.4rem 1.25rem 3rem;
  line-height: 1.55;
  font-size: 13px;
  -webkit-font-smoothing: antialiased;
}
/* macOS terminal window */
.term {
  max-width: 1000px;
  margin: 0 auto;
  background: var(--bg);
  border: 1px solid var(--titlebar-border);
  border-radius: 10px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22), 0 2px 6px rgba(0, 0, 0, 0.10);
  overflow: hidden;
}
.term-bar {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  height: 38px;
  padding: 0 0.85rem;
  background: linear-gradient(var(--titlebar-top), var(--titlebar-bottom));
  border-bottom: 1px solid var(--titlebar-border);
}
.term-title {
  position: absolute;
  left: 0; right: 0;
  text-align: center;
  color: #5b5b5f;
  font-size: 0.76rem;
  letter-spacing: 0.01em;
  pointer-events: none;
}
.term-body { padding: 1.1rem 1.5rem 1.8rem; }
/* macOS shell greeting + prompt */
.login { color: var(--muted); font-size: 0.8rem; margin: 0 0 0.15rem; }
.prompt { font-size: 0.86rem; margin: 0 0 1.4rem; color: var(--text); }
.prompt .user { color: var(--prompt); }
.prompt .path { color: var(--blue); }
.prompt .pct { color: var(--muted); }
.cursor {
  display: inline-block;
  width: 0.5em;
  height: 1.05em;
  background: var(--text);
  margin-left: 3px;
  vertical-align: text-bottom;
  animation: blink 1.1s steps(2, start) infinite;
}
@keyframes blink { 0%, 50% { opacity: 1; } 50.01%, 100% { opacity: 0; } }
.meta .ok { color: var(--prompt); }
.meta .bad { color: var(--err); }
/* Group dividers for organization */
.group { margin: 1.8rem 0 0.4rem; }
.group:first-of-type { margin-top: 0.6rem; }
.group-title {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 0.7rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--line);
}
section {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 8px;
  margin-bottom: 0.8rem;
  padding: 0.7rem 1rem 1rem;
}
section h2 {
  font-size: 0.82rem;
  margin: 0 0 0.8rem;
  padding-bottom: 0.5rem;
  color: var(--text);
  border-bottom: 1px solid var(--line);
  font-weight: 600;
  display: flex;
  align-items: center;
}
section h2::before {
  content: "%";
  color: var(--prompt);
  margin-right: 0.5rem;
  font-weight: 600;
}
/* Collapsible section (e.g. tokens) */
details.box > summary {
  list-style: none;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text);
  padding-bottom: 0.5rem;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
}
details.box > summary::-webkit-details-marker { display: none; }
details.box > summary::before {
  content: "%";
  color: var(--prompt);
  margin-right: 0.5rem;
  font-weight: 600;
}
details.box > summary .chev {
  margin-left: 0.6rem;
  color: var(--muted);
  transition: transform 0.15s ease;
}
details.box[open] > summary .chev { transform: rotate(90deg); }
details.box > summary .count { color: var(--muted); font-weight: 400; margin-left: 0.4rem; }
details.box > summary:hover { color: var(--blue); }
/* status badges */
.badge {
  display: inline-block;
  font-size: 0.68rem;
  margin-left: auto;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 0.05rem 0.45rem;
  border-radius: 4px;
}
.badge-ok { color: var(--prompt); background: rgba(26, 127, 55, 0.10); }
.badge-warn { color: var(--err); background: rgba(192, 57, 43, 0.10); }
.badge-pending { color: var(--muted); background: var(--panel-alt); }
.source-wrap { overflow-x: auto; }
.source { border-collapse: collapse; width: 100%; font-size: 0.82rem; }
.source td { vertical-align: top; padding: 0 0.35rem; }
.source .ln {
  color: var(--faint);
  text-align: right;
  user-select: none;
  width: 2.5rem;
  padding-right: 0.85rem;
}
.source .code { white-space: pre; }
.source tr.error-line { background: var(--err-bg); }
.source tr.error-line .ln { color: var(--err); font-weight: 600; }
.err-marker { color: var(--err); font-size: 0.78rem; white-space: pre; }
.diag {
  border-left: 3px solid var(--err);
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
  background: var(--err-bg);
  border-radius: 0 5px 5px 0;
}
.diag strong { color: var(--err); }
.diag .hint { color: #7a6a52; margin-top: 0.35rem; font-size: 0.8rem; }
.diag .hint::before { content: "\\21B3  "; }
.tok-keyword { color: var(--kw); }
.tok-operator { color: var(--op); }
.tok-punct { color: var(--punct); }
.tok-ident { color: var(--ident); }
.tok-integer { color: var(--num); }
.tok-string { color: var(--str); }
.tok-other { color: var(--other); }
table.data { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
table.data th, table.data td {
  border-bottom: 1px solid var(--line);
  padding: 0.4rem 0.6rem;
  text-align: left;
}
table.data thead th {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--line-strong);
  background: var(--panel-alt);
}
table.data tbody tr:last-child td { border-bottom: none; }
table.data tbody tr:hover td { background: var(--panel-alt); }
pre.tree {
  margin: 0;
  font-size: 0.78rem;
  overflow-x: auto;
  white-space: pre;
  color: #4b4b50;
}
/* program output console pane */
ul.console {
  list-style: none;
  margin: 0;
  padding: 0.7rem 0.85rem;
  background: var(--panel-alt);
  border: 1px solid var(--line);
  border-radius: 6px;
}
ul.console li { white-space: pre-wrap; }
ul.console li::before { content: "\\203A  "; color: var(--prompt); }
.empty { color: var(--muted); font-size: 0.84rem; margin: 0.2rem 0; }
.empty::before { content: "# "; color: var(--faint); }
.subhead {
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.03em;
  margin: 0.9rem 0 0.4rem;
}
.subhead:first-child { margin-top: 0; }
.legend { font-size: 0.74rem; color: var(--muted); margin-top: 0.7rem; }
.legend span { margin-right: 0.85rem; }
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
        return '<span class="badge badge-ok">ok</span>'
    if ok is False:
        return '<span class="badge badge-warn">error</span>'
    return '<span class="badge badge-pending">n/a</span>'


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
        '<span class="tok-keyword">palabra clave</span>'
        '<span class="tok-ident">identificador</span>'
        '<span class="tok-integer">entero</span>'
        '<span class="tok-string">cadena</span>'
        '<span class="tok-operator">operador</span>'
        '<span class="tok-punct">puntuación</span>'
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


def _render_result(report: CompilationReport) -> str:
    """Resultado final del programa: los errores si los hay, o la salida producida."""
    if report.diagnostics:
        return _render_diagnostics(report)
    if report.program_output:
        body = "".join(f"<li>{_escape(line)}</li>" for line in report.program_output)
        return f'<ul class="console">{body}</ul>'
    return (
        '<p class="empty">El programa compiló sin errores y no produjo salida '
        "(no hay sentencias write).</p>"
    )


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


def _render_extras(report: CompilationReport) -> str:
    if not report.arrays and not report.functions:
        return (
            '<p class="empty">Este programa no usa arreglos ni funciones '
            "(características extra).</p>"
        )

    parts: list[str] = []

    if report.arrays:
        rows = "".join(
            f"<tr><td class=\"tok-ident\">{_escape(a.name)}</td>"
            f"<td>{a.size}</td><td>0 .. {a.size - 1}</td></tr>"
            for a in report.arrays
        )
        parts.append('<p class="subhead">Arreglos</p>')
        parts.append(
            "<table class=\"data\"><thead><tr><th>Nombre</th><th>Tamaño</th>"
            f"<th>Índices válidos</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    else:
        parts.append('<p class="subhead">Arreglos</p>')
        parts.append('<p class="empty">Ninguno declarado.</p>')

    if report.functions:
        rows = "".join(
            f"<tr><td class=\"tok-ident\">{_escape(f.name)}</td>"
            f"<td class=\"tok-keyword\">{_escape(f.signature)}</td>"
            f"<td>{len(f.params)}</td></tr>"
            for f in report.functions
        )
        parts.append('<p class="subhead">Funciones</p>')
        parts.append(
            "<table class=\"data\"><thead><tr><th>Nombre</th><th>Firma</th>"
            f"<th>Parámetros</th></tr></thead><tbody>{rows}</tbody></table>"
        )
    else:
        parts.append('<p class="subhead">Funciones</p>')
        parts.append('<p class="empty">Ninguna declarada.</p>')

    return "".join(parts)


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
        '<span class="ok">ok</span>'
        if report.ok
        else '<span class="bad">con errores</span>'
    )
    n_tokens = len(report.tokens)
    n_diag = len(report.diagnostics)
    has_extras = bool(report.arrays or report.functions)
    extras_badge = _badge(True if has_extras else None)
    parse_available = report.phases_available.get("parse")
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
      <span class="term-title">compilador — {name}</span>
    </div>
    <div class="term-body">
      <p class="login">Informe de compilación &middot; {n_tokens} tokens &middot; \
{n_diag} diagnóstico(s) &middot; estado: <span class="meta">{status_html}</span></p>
      <p class="prompt"><span class="user">compilador</span> <span class="path">~</span> \
<span class="pct">%</span> compilar {_escape(name)}<span class="cursor"></span></p>

      <div class="group">
        <p class="group-title">Resultado</p>
        <section>
          <h2>Salida o error {_badge(False if report.diagnostics else True)}</h2>
          {_render_result(report)}
        </section>
      </div>

      <div class="group">
        <p class="group-title">Análisis (léxico y sintáctico)</p>
        <section>
          <h2>Código fuente {_badge(lex_ok)}</h2>
          {_render_source(report)}
        </section>
        <section>
          <details class="box">
            <summary>Tokens <span class="count">({n_tokens})</span>{_badge(lex_ok)}\
<span class="chev">&#8250;</span></summary>
            {_render_tokens_table(report)}
          </details>
        </section>
        <section>
          <h2>Árbol de parseo {_badge(parse_ok if parse_available else None)}</h2>
          {parse_section}
        </section>
      </div>

      <div class="group">
        <p class="group-title">Extras (arreglos y funciones)</p>
        <section>
          <h2>Arreglos y funciones {extras_badge}</h2>
          {_render_extras(report)}
        </section>
      </div>

      <div class="group">
        <p class="group-title">Código intermedio</p>
        <section>
          <h2>Cuádruplos (IR) {_badge(None if not report.quadruples else True)}</h2>
          {_render_quadruples(report)}
        </section>
      </div>

      <div class="group">
        <p class="group-title">Ejecución (runtime)</p>
        <section>
          <h2>Memoria (tabla de símbolos) {_badge(None if not report.memory else True)}</h2>
          {_render_memory(report)}
        </section>
        <section>
          <h2>Salida del programa (write) {_badge(None if not report.program_output else True)}</h2>
          {_render_output(report)}
        </section>
      </div>
    </div>
  </div>
</body>
</html>"""


def write_report_html(report: CompilationReport, output: Path) -> Path:
    output.write_text(render_html(report), encoding="utf-8")
    return output
