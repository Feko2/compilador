---
name: Compilador Python con Lark
overview: Construir el compilador por fases muy acotadas, usando los programas en pruebas/ como contrato con el profesor (tokens y formas de frase visibles ahí). Cada fase termina en algo pequeño que puedes explicar en oral.
todos:
  - id: phase0-contract-from-pruebas
    content: Inventariar tokens y reglas mínimas a partir de pruebas/*.txt; definir formato de errores y convención de commits por fase.
    status: completed
  - id: phase1-lexer-only
    content: Implementar solo el analizador léxico que reconozca todo lo que aparece en los cuatro archivos de pruebas/ (sin parser completo aún).
    status: completed
  - id: phase2-parse-skeleton
    content: Gramática Lark mínima para program main { var ...; begin; ... end; } más write, asignación := y expresiones aritméticas; validar con tests pequeños (fragmentos de pruebas/ sin if/while/for aún).
    status: completed
  - id: phase3-parse-control
    content: Extender gramática para if/then/else, while/do y for (...); validar pruebaIf.txt y pruebaWhile.txt.
    status: pending
  - id: phase4-ast
    content: Parse tree a AST propio; pruebas de estructura sobre fragmentos de pruebas/.
    status: pending
  - id: phase5-semantics
    content: Tabla de símbolos y chequeos básicos; usar pruebaErrores.txt como caso de error semántico esperado (and entre bool e int).
    status: pending
  - id: phase6-ir-optional
    content: IR mínimo y traducción desde AST (solo si el curso lo exige en esta entrega).
    status: pending
  - id: phase7-runtime-optional
    content: Intérprete o evaluador del IR (solo si aplica).
    status: pending
  - id: phase8-exposicion
    content: Notas por fase (qué hace el módulo, flujo de datos) y mapa de cada archivo en pruebas/ a la fase que lo valida.
    status: pending
isProject: false
---

# Plan por fases (alineado con `pruebas/`)

## Objetivo
Avanzar **solo una capa a la vez** (léxico → sintaxis mínima → sintaxis completa de los ejemplos → AST → semántica → IR/ejecución si aplica), de modo que en cada entrega puedas decir **qué archivo toca qué responsabilidad** y **cómo fluyen los datos** hasta esa capa.

Los programas en **`pruebas/`** son la referencia práctica del lenguaje que pide el profesor: ahí está el conjunto de **palabras reservadas, operadores y literales** que el léxico debe emitir y el parser debe aceptar.

## Contrato con el profesor: archivos en `pruebas/`

| Archivo | Qué ejercita (para estudiar y para probar) |
|---------|---------------------------------------------|
| [`pruebas/pruebaFor.txt`](../pruebas/pruebaFor.txt) | `program`, `main`, `var`, `:`, `int`, `begin`/`end`, `:=`, `for` con `(init; cond; incr)`, cuerpo con `{ }`, `write`, aritmética `*`, comparación `<`. |
| [`pruebas/pruebaWhile.txt`](../pruebas/pruebaWhile.txt) | `while`, `do`, condición con `>=`, decremento `n--` (tokens `--` o postfix según definan), asignación y aritmética. |
| [`pruebas/pruebaIf.txt`](../pruebas/pruebaIf.txt) | `if`/`then`/`else`, anidamiento, comparaciones `>` y `<`, expresiones mixtas con paréntesis. |
| [`pruebas/pruebaErrores.txt`](../pruebas/pruebaErrores.txt) | Igual que if pero condición con `and` entre una comparación y una expresión entera: sirve como **caso semántico inválido** una vez exista chequeo de tipos. |

**Regla de oro:** no ampliar el lenguaje en código hasta que los cuatro `.txt` tokenicen y (según la fase) parseen como acordes con esta tabla.

## Estructura de código sugerida (crecer con el repo)
- `src/lexer/` — definición de tokens / scanner (Fase 1).
- `src/grammar/` — archivo `.lark` (Fases 2–3).
- `src/ast/` — nodos y transformación desde Lark (Fase 4).
- `src/semantics/` — tabla de símbolos y diagnósticos (Fase 5).
- `src/ir/`, `src/runtime/` — solo si el curso lo pide (Fases 6–7).
- `src/main.py` — orquestación del pipeline; al principio puede invocar solo el léxico sobre un path a `pruebas/...`.

Las pruebas automáticas pueden vivir en `tests/` leyendo los mismos archivos con `pathlib` para no duplicar el texto del profesor.

## Fase 0 — Contrato y vocabulario (sin “features extra”)
- Recorrer los cuatro `.txt` y listar: palabras clave, operadores, delimitadores, literales (enteros y cadenas `"..."`), identificadores.
- Decidir mensajes de error (línea/columna, código corto).
- Un commit inicial o rama `fase-0-contrato` con solo documentación y esqueleto vacío si quieres.

## Fase 1 — **Solo léxico**
- Salida: secuencia de tokens para cada archivo en `pruebas/` (puede imprimirse o serializarse en tests).
- **Criterio de cierre:** los cuatro archivos se tokenizan sin errores; puedes explicar en viva voz qué es cada clase de token y dónde está en el código.
- **No** incluir aún AST ni tabla de símbolos.

## Fase 2 — Sintaxis mínima (sin todo el control de flujo)
- Cubrir: declaración `var`, tipos, bloque `program main { ... }`, `begin;` / `end;`, `write(...)`, asignación `:=`, expresiones aritméticas y paréntesis.
- **Criterio de cierre:** tests con fragmentos extraídos de `pruebas/*.txt` (mismo texto de tokens, pero sin `if`/`while`/`for` hasta la siguiente fase). Objetivo: poder explicar la gramática “núcleo” sin mezclar control de flujo.

## Fase 3 — Sintaxis completa de los ejemplos
- Añadir `if`/`then`/`else`, `while`/`do`, `for` con la forma exacta de los `.txt`.
- **Criterio de cierre:** parse sin error de `pruebaIf.txt`, `pruebaWhile.txt`, `pruebaFor.txt` (y `pruebaErrores.txt` a nivel **sintáctico**).

## Fase 4 — AST
- Traducción a árbol propio; tests que comparen forma del AST en entradas pequeñas extraídas de `pruebas/`.

## Fase 5 — Semántica estática
- Tabla de símbolos, tipos, uso de variables.
- **`pruebaErrores.txt`:** debe reportar error semántico (por ejemplo `and` entre booleano y entero); los otros tres deben pasar análisis si el lenguaje es coherente con enteros y condiciones booleanas.

## Fases 6–7 — IR y ejecución (opcional según enunciado)
- Solo abrir estas fases cuando las anteriores estén cerradas con pruebas y notas.

## Fase 8 — Material para preguntas del profesor
- Por cada fase, tres líneas en el mensaje del commit o del PR: **entrada**, **salida**, **archivos tocados** (así queda trazable sin añadir más documentos).
- Diagrama simple del pipeline en papel o markdown: `pruebas/*.txt` → lexer → parser → AST → semántica → (IR) → (runtime).

## Estrategia de estudio (pocas líneas nuevas por vez)
- Cerrar fase con: una demo (`main` o test) + 3–5 aserciones + notas breves.
- **Commits o ramas por fase** (`fase-1-lexer`, etc.) para narrar la evolución al revisar.

## Nota sobre Lark
Lark puede hacer léxico y parser juntos; aun así conviene **tratar la Fase 1 como “entender los tokens”** (reglas `TOKEN` / `terminals` claras o lexer aparte). Eso prepara las respuestas tipo “¿cómo distingues `:=` de `:`?” o “¿qué token es `--`?”.
