# pyrapidparser

Parser, syntax tree tools and Python translator for **ABB RAPID**, the programming
language of ABB robot controllers.

The project contains:

| Tool               | What it does                                                          |
| ------------------ | --------------------------------------------------------------------- |
| `rapid_parser.py`  | lexer and parser (PLY) that build the syntax tree (`rapid_ast`)       |
| `rapidvalidate.py` | static semantic checks after parsing (names, types, arguments, ...)   |
| `rapid2rapid.py`   | writes the tree back as RAPID (formatting and round-trip check)       |
| `rapid2py.py`      | translates RAPID modules into an executable Python program            |
| `run/pyrapid.py`   | runtime used by the generated code (symbols, types, scopes, errors)   |

The reference for syntax and semantics is the ABB *Technical reference manual - RAPID
kernel* (3HAC050946-001), together with the *RAPID Overview* (3HAC050947-001) and
*Instructions, Functions and Data types* (3HAC050917-001).

## Requirements

- Python 3.9 or later
- [ply](https://pypi.org/project/ply/) 3.11
- [hatch](https://hatch.pypa.io/) for development (optional)

```sh
pip install ply
```

The module `rapid_ast.py` is generated from `_rapid_ast.cfg` and is not in the repository.
Generate it before the first use (with hatch the `test` and `typecheck` scripts and the
package build do it for you):

```sh
python _ast_gen.py
```

## Usage

The examples use this module, `hello.mod`:

```
MODULE hello
    VAR num total := 0;
    PROC main()
        FOR i FROM 1 TO 10 DO
            total := total + i;
        ENDFOR
        TPWrite "total = " \Num:=total;
    ENDPROC
ENDMODULE
```

### Validation

```sh
python rapidvalidate.py hello.mod
```

The command checks all the modules of the task together with the standard modules in
`default/*.sys`. It prints the diagnostics as `file:line: severity: message [code]` and
exits with 1 when it finds errors. For example:

```
bad.mod:4: error: cannot assign to the constant k [assign-constant]
bad.mod:5: error: undefined procedure foo [undefined-routine]
```

The checks include:

- duplicate names and scope rules;
- unknown types and aliases;
- array dimensions and indexes;
- constant and literal expressions;
- value classes and type compatibility in assignments and operators;
- aggregates;
- procedure and function calls: number, name, order and mode of the arguments, optional
  and mutually exclusive arguments, `\switch`;
- assignments to constants and read-only data;
- labels and `GOTO`, including jumps into a statement list;
- `RETURN`, error handlers and `RAISE`;
- length of identifiers and strings.

| Option             | Effect                                              |
| ------------------ | --------------------------------------------------- |
| `-s`               | do not load the standard modules                    |
| `--check-standard` | also report the diagnostics of the standard modules |

From Python:

```python
import rapidvalidate

for d in rapidvalidate.validate_files(["hello.mod"]):
    print(d.file, d.line, d.severity, d.code, d.message)
```

### Translation to Python

```sh
python rapid2py.py -i hello.mod -d out -f hello.py -e hello.main
cd out
PYTHONPATH=../run:.. python hello.py
```

`rapid2py` validates the program before translating it and generates nothing if there are
errors. The generated program imports `pyrapid` (folder `run/`) and the project modules,
which is why `PYTHONPATH` is needed.

| Option             | Effect                                                            |
| ------------------ | ----------------------------------------------------------------- |
| `-i FILE`          | module to translate (repeat it for more modules of the same task) |
| `-d DIR`           | output folder, it must exist                                      |
| `-f FILE`          | output file (default `rapid_program.py`)                          |
| `-e [MODULE.]PROC` | procedure called as entry point                                   |
| `-r`               | run the entry point after the translation                         |
| `-s`               | do not include the standard symbols of `default/*.sys`            |
| `--no-validate`    | skip the checks of `rapidvalidate`                                |

Comment lines starting with `!python:` are copied as they are into the generated code.
This is how `default/standard.sys` implements the system instructions in Python
(`TPWrite`, `WaitTime`, ...):

```
PROC WaitTime(\switch InPos, num Time)
    !python:import time
    !python:time.sleep(pyrapid.Symbols().GetSymbol("Time").data.Get())
ENDPROC
```

How the constructs without a direct Python equivalent are translated:

- **GOTO**: every statement list that contains labels becomes a dispatch loop, and `GOTO`
  raises `pyrapid.Goto`.
- **FOR**: the loop variable exists only while the loop runs and hides any variable with
  the same name.
- **Error handlers**: `RETRY`, `TRYNEXT`, `RAISE` and `RETURN` are implemented.

### Rewriting as RAPID

```sh
python rapid2rapid.py -i hello.mod -d out -f hello.mod
```

The command reads the module and writes it back with a uniform formatting. Parentheses are
added only where they are needed to keep the same expression tree. The tests check that
rewriting the result a second time gives the same text.

## Supported language

- **Case**: the language is not case sensitive, as the manual says (Overview 1.1.1).
  `PROC`, `proc` and `Proc` are the same keyword, `Total` and `total` the same name.
- **Strings**: only the escapes of the manual (kernel 2.7): `\hh` (hexadecimal character
  code), `\\` and `""`. A string with any other escape is a lexer error.
- **Expressions**: priority and associativity as in the manual (kernel 3.1). Operators of
  the same priority are evaluated from left to right, and `NOT` applies to the first
  logical term.

The missing features are listed in [todo.md](todo.md). Among them:

- interrupts and `CONNECT`;
- long jumps in error handlers;
- semantics of `BACKWARD` and `UNDO`;
- motion instructions (`MoveJ`, `MoveL`, ...);
- installed data types such as `signaldi`.

## Layout

```
rapid_lexer.py        RAPID lexer (PLY)
rapid_parser.py       grammar and AST construction
_rapid_ast.cfg        definition of the AST nodes
_ast_gen.py           generates rapid_ast.py from _rapid_ast.cfg
ast_gen.py            generator used by _ast_gen.py
plyparser.py          common parser support (coordinates, errors)
browse_rapid_ast.py   base visitor and evaluation of constant expressions
rapidvalidate.py      semantic validation
rapid2rapid.py        AST -> RAPID
rapid2py.py           AST -> Python
run/pyrapid.py        runtime of the generated code
default/standard.sys  declarations and implementations of the standard types and routines
test/                 RAPID test modules
test/exec/            programs translated and run, with the expected output (.out)
Pallettizer/          example of a real program
doc/abb/official/     ABB manuals (not in the repository, see below)
```

## Development

```sh
hatch run test          # all the tests, including mypy --strict and ruff format --check
hatch run cov           # tests with coverage
hatch run typecheck     # mypy --strict only
hatch run format        # reformat the code with ruff
hatch run gen-ast       # regenerate rapid_ast.py
```

The tests:

| Test                       | What it checks                                                     |
| -------------------------- | ------------------------------------------------------------------ |
| `test_rapid.py`            | parsing of the modules in `test/` and visit of the tree            |
| `test_roundtrip.py`        | the second rewrite with rapid2rapid is identical to the first      |
| `test_expressions.py`      | operator priority and associativity                                |
| `test_strings.py`          | string literals and escapes                                        |
| `test_case_insensitive.py` | keywords and names regardless of case                              |
| `test_rapidvalidate.py`    | one case for each diagnostic, and the invalid files in `test/`     |
| `test_rapid2py.py`         | the generated Python compiles, the `test/exec/` programs run right |
| `test_quality.py`          | mypy strict and ruff formatting                                    |

The project code is typed and must pass `mypy --strict`. The generated files are excluded
(`rapid_ast.py` and the PLY tables `lextab.py` and `yacctab.py`). The formatting is the one
of `ruff format`, with lines of at most 100 characters.

Code comments and documentation are in English.

### ABB manuals

The official manuals are ABB copyright and are not distributed with the project. Download
them from the [ABB Library](https://library.e.abb.com/) and put them in
`doc/abb/official/`, which is excluded by `.gitignore`.
