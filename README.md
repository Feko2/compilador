# Compilador

Compilador por fases para un lenguaje imperativo sencillo (estilo Pascal/C),
escrito en Python usando [Lark](https://github.com/lark-parser/lark).

Implementa el pipeline completo:

```
texto fuente → léxico → sintaxis → AST → semántica → ejecución → salida
```

Además genera un **informe HTML** con todas las fases (tokens coloreados,
árbol de parseo, código intermedio, memoria y salida del programa).

---

## Requisitos

- Python 3.9 o superior
- [`lark`](https://pypi.org/project/lark/) `>=1.1,<2` (única dependencia)

## Instalación

```bash
# 1. Crear y activar un entorno virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 2. Instalar el proyecto en modo editable (deja disponible `python -m compilador`)
pip install -e .

# Para correr las pruebas también:
pip install -e ".[dev]"
```

> Si prefieres no instalar, puedes ejecutar todo anteponiendo `PYTHONPATH=src`,
> por ejemplo: `PYTHONPATH=src python3 -m compilador archivo.txt --run`.

---

## Uso

La interfaz de línea de comandos recibe un archivo fuente y un modo:

```bash
python -m compilador <archivo.txt> [modo]
```

| Modo        | Qué hace                                                              |
|-------------|----------------------------------------------------------------------|
| *(ninguno)* | Muestra la lista de **tokens** (tipo, valor, línea, columna).        |
| `--parse`   | Muestra el **árbol de parseo** (sintaxis).                           |
| `--check`   | Solo **análisis semántico**: reporta errores de tipos/declaración.   |
| `--run`     | **Ejecuta** el programa y muestra la salida de `write(...)`.         |
| `--report`  | Genera un **informe HTML** completo (`archivo.txt.report.html`).      |

Opciones extra:

- `--report salida.html` — escribe el informe en una ruta específica.
- `--no-parse` — junto a `--report`, solo realiza el análisis léxico.

### Ejemplos

```bash
# Ver tokens
python -m compilador pruebas/pruebaFor.txt

# Ver el árbol de parseo
python -m compilador pruebas/pruebaWhile.txt --parse

# Verificar errores semánticos (sin ejecutar)
python -m compilador pruebas/pruebaErrores.txt --check

# Ejecutar el programa
python -m compilador pruebas/pruebaFuncion.txt --run

# Generar el informe HTML y abrirlo (macOS)
python -m compilador pruebas/pruebaArray.txt --report
open pruebas/pruebaArray.txt.report.html
```

Ejemplo de ejecución:

```bash
$ python -m compilador pruebas/pruebaFuncion.txt --run
prueba funcion
7
25
14
```

---

## El lenguaje

### Estructura de un programa

```
program main {
    var i, n, x : int;          // declaraciones

    function cuadrado(n : int) : int {   // funciones (opcional)
        begin;
            cuadrado := n * n;           // retorno = asignar al nombre de la función
        end;
    }

    begin;                      // cuerpo principal (ojo: begin; y end; con ';')
        x := cuadrado(5);
        write("resultado:");
        write(x);
    end;
}
```

### Tipos

- `int` — entero.
- `array [N] of int` — arreglo de tamaño fijo `N`, índices válidos `0 .. N-1`.

```
var nums : array [5] of int;
nums[0] := 10;
write(nums[0]);
```

### Sentencias

| Sentencia        | Sintaxis                                              |
|------------------|-------------------------------------------------------|
| Asignación       | `x := expr;`  /  `nums[i] := expr;`                   |
| Escritura        | `write(expr);`  /  `write("texto");`                  |
| Condicional      | `if (cond) then { ... } else { ... }`  (`else if` permitido) |
| Bucle `while`    | `while (cond) do { ... }`                             |
| Bucle `for`      | `for (i := 0; cond; i++) { ... }`                     |
| Incremento/decr. | `i++;`  /  `i--;`  (también `i++` / `i--` en el `for`) |

### Expresiones y operadores

- **Aritméticos:** `+`, `-`, `*`, `/`, `%`, y menos unario (`-x`).
- **Comparación:** `>`, `<`, `>=`, `<=`, `==`, `!=`.
- **Lógicos:** `and`, `or`, `not` — precedencia: `or` < `and` < `not` < comparación.
- Paréntesis `( ... )` para agrupar.

```
if (a >= b and not (c == 0)) then { ... }
x := (a + b) * -2 / 3;
```

### Funciones

- Se declaran **antes** del `begin;` principal.
- El **valor de retorno** se da asignando al nombre de la función (estilo Pascal):
  `suma := a + b;`
- Se invocan dentro de expresiones: `r := suma(3, cuadrado(2));`

---

## Archivos de prueba (`pruebas/`)

| Archivo                 | Demuestra                                              |
|-------------------------|-------------------------------------------------------|
| `pruebaFor.txt`         | Bucle `for`, `++`, comparación `<`, aritmética.       |
| `pruebaWhile.txt`       | Bucle `while`, `>=`, decremento `--`.                 |
| `pruebaIf.txt`          | `if/then/else` anidados, comparaciones `>` y `<`.     |
| `pruebaErrores.txt`     | Caso con **error semántico** (condición no booleana). |
| `pruebaArray.txt`       | Arreglos: declaración, acceso `arr[i]`, recorrido.    |
| `pruebaFuncion.txt`     | Funciones con parámetros y llamadas anidadas.         |
| `pruebaOperadores.txt`  | Todos los operadores (`<=`, `==`, `!=`, `or`, `not`, `/`, `%`, unario). |

---

## Manejo de errores

El compilador reporta errores con fase, línea y columna, y una pista de ayuda:

- **Léxicos** — carácter no reconocido.
- **Sintácticos** — token inesperado / estructura inválida.
- **Semánticos** — variable no declarada, tipos incompatibles, condición no
  booleana, índice no entero, función inexistente o con argumentos incorrectos.
- **En ejecución** — índice de arreglo fuera de rango, división/módulo por cero,
  variable no inicializada.

```bash
$ python -m compilador pruebas/pruebaErrores.txt --check
semantic: Se usa una expresión entera donde se espera una condición booleana.
semantic: El operando derecho de 'and' no es booleano.
```

---

## Pruebas

```bash
pytest            # corre toda la suite (requiere: pip install -e ".[dev]")
pytest -q         # salida resumida
```

La configuración de `pytest` ya añade `src/` al path (`pyproject.toml`), así que
no se necesita instalar el paquete para correr las pruebas.

---

## Estructura del proyecto

```
src/compilador/
├── __main__.py          # CLI (modos --parse, --check, --run, --report)
├── contract.py          # contrato léxico: keywords, operadores, tipos de token
├── lexer/               # Fase 1: análisis léxico
│   ├── terminals.lark   #   definición de terminales (compartida)
│   ├── tokens.lark      #   gramática de tokens
│   └── scanner.py
├── grammar/program.lark # Fases 2-3: gramática completa (LALR)
├── parser.py            # carga la gramática y parsea
├── ast_nodes.py         # Fase 4: nodos del AST (dataclasses)
├── ast_builder.py       #   transforma el parse tree → AST
├── semantic.py          # Fase 5: tabla de símbolos y chequeo de tipos
├── interpreter.py       # Fases 6-7: ejecución + cuádruplos (código intermedio)
├── errors.py            # mensajes de error con línea/columna
└── viz/                 # informe HTML (tokens, árbol, IR, memoria, salida)

pruebas/                 # programas de ejemplo
tests/                   # suite de pytest
```

## Fases del compilador

1. **Léxico** — convierte el texto en tokens.
2. **Sintáctico** — construye el árbol de parseo con una gramática LALR.
3. **AST** — transforma el árbol de parseo en un AST propio tipado.
4. **Semántico** — tabla de símbolos, chequeo de tipos y de declaraciones.
5. **Ejecución** — intérprete *tree-walking* que evalúa el programa y, de paso,
   emite **cuádruplos** (representación intermedia clásica).
