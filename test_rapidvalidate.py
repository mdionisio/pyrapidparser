"""rapidvalidate: static semantic checks of the RAPID kernel manual (3HAC050946-001).

Each case is a small task module and the expected diagnostic codes; the standard
modules default/*.sys are loaded as in rapid2py.
"""

import os
from typing import Any

import pytest

import rapid_parser
import rapidvalidate

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_DIR, "test")

_STANDARD: list[Any] = []
PARSER = rapid_parser.RAPIDParser(
    lex_optimize=True, yacc_debug=False, yacc_optimize=False, start_from="module_declaration_list"
)


def standard_modules() -> list[Any]:
    if not _STANDARD:
        modules, errors = rapidvalidate.parse_files(rapidvalidate.standard_files())
        assert not errors
        _STANDARD.extend(modules)
    return _STANDARD


def diagnostics(text: str) -> list[rapidvalidate.Diagnostic]:
    path = os.path.join(TEST_DIR, "case.mod")
    parser = PARSER
    modules = parser.parse(text, path).module_list
    result = rapidvalidate.validate(standard_modules() + modules)
    return [d for d in result if d.file == path]


def codes(text: str) -> list[str]:
    return sorted(d.code for d in diagnostics(text))


def module(body: str, name: str = "m1") -> str:
    return "MODULE %s\n%s\nENDMODULE\n" % (name, body)


def proc(body: str, decl: str = "", params: str = "") -> str:
    return module("%s\n    PROC main(%s)\n%s\n    ENDPROC" % (decl, params, body))


CASES = [
    # --- valid programs: no diagnostic
    ("valid program", proc('        x := x + 1;\n        TPWrite "x";', "    VAR num x := 0;"), []),
    (
        "valid record and aggregate",
        module(
            "    RECORD item\n        num count;\n        pos p;\n    ENDRECORD\n"
            "    CONST item it := [1, [0, 0, 0]];\n    VAR num n := it.count + it.p.x;"
        ),
        [],
    ),
    (
        "valid optional arguments",
        module(
            "    PROC q(num a \\switch on | switch off, \\num b)\n    ENDPROC\n"
            "    PROC p(\\num c)\n        q 1 \\on \\b := 2;\n        q 1;\n        q 1 \\off \\b ? c;\n"
            "    ENDPROC"
        ),
        [],
    ),
    (
        "valid error handler",
        proc("        RAISE 10;\n    ERROR (10)\n        RETRY;\n        TRYNEXT;\n        RAISE;"),
        [],
    ),
    (
        "valid labels and goto",
        proc(
            "        start:\n        IF x > 1 THEN\n            GOTO start;\n        ENDIF",
            "    VAR num x;",
        ),
        [],
    ),
    # --- 2.3 Identifiers (reserved words are rejected by the lexer)
    ("identifier too long", module("    VAR num %s;" % ("a" * 33)), ["identifier-too-long"]),
    # --- 2.13 The type string
    ("string of 80 characters", module('    VAR string s := "%s";' % ("x" * 80)), []),
    ("string too long", module('    VAR string s := "%s";' % ("x" * 81)), ["string-too-long"]),
    ("string with character codes", module('    VAR string s := "%s";' % ("\\07" * 80)), []),
    ("string escapes", module('    VAR string s := "a\\\\b""c\\41";'), []),
    # --- 2.12, 2.20, 5.3 scope rules
    (
        "duplicate module object",
        module("    RECORD r1\n        num a;\n    ENDRECORD\n    VAR num R1;"),
        ["duplicate-name"],
    ),
    (
        "global clashes with standard module",
        module("    PROC TPWrite()\n    ENDPROC"),
        ["duplicate-global"],
    ),
    ("local hides global", module("    LOCAL PROC TPWrite()\n    ENDPROC"), []),
    ("global clashes with module name", module("    VAR num m1;"), ["module-name-clash"]),
    ("duplicate routine data object", proc("", "", "num a, num A"), ["duplicate-name"]),
    (
        "routine data object clashes with parameter",
        proc("        VAR num a;", "", "num a"),
        ["duplicate-name"],
    ),
    # --- 9.2 Module attributes
    ("attribute repeated", "MODULE m2(SYSMODULE, SYSMODULE)\nENDMODULE\n", ["module-attribute"]),
    ("attribute order", "MODULE m2(NOSTEPIN, SYSMODULE)\nENDMODULE\n", ["module-attribute"]),
    ("attribute exclusion", "MODULE m2(NOVIEW, READONLY)\nENDMODULE\n", ["module-attribute"]),
    # --- 2.11-2.15 data types
    ("unknown type", module("    VAR pone p;"), ["unknown-type"]),
    ("not a type", module("    VAR num a;\n    VAR a b;"), ["not-a-type"]),
    ("alias of alias", module("    ALIAS num level;\n    ALIAS level level2;"), ["alias-of-alias"]),
    ("alias of builtin alias", module("    ALIAS errnum myerr;"), ["alias-of-alias"]),
    (
        "duplicate record component",
        module("    RECORD r1\n        num a;\n        num a;\n    ENDRECORD"),
        ["duplicate-name"],
    ),
    # --- 2.18-2.24 data declarations
    (
        "local in routine",
        module("    PROC p()\n        LOCAL VAR num a;\n    ENDPROC"),
        ["local-in-routine"],
    ),
    (
        "persistent in routine",
        module("    PROC p()\n        PERS num a := 1;\n    ENDPROC"),
        ["pers-in-routine"],
    ),
    ("array degree", module("    VAR num a{2,2,2,2};"), ["array-degree"]),
    ("array dimension", module("    VAR num a{0};"), ["array-dimension"]),
    ("array dimension not integer", module("    VAR num a{1.5};"), ["array-dimension"]),
    ("constant without value", module("    CONST num c;"), ["missing-value"]),
    ("local persistent without value", module("    LOCAL PERS num c;"), ["missing-value"]),
    ("global persistent without value", module("    PERS num c;"), []),
    ("variable not constant", module("    VAR num a := 1;\n    VAR num b := a;"), ["not-constant"]),
    ("constant expression", module("    CONST num a := 1;\n    VAR num b := a * 2;"), []),
    ("function call not constant", module("    VAR num b := Abs(1);"), ["not-constant"]),
    ("persistent literal", module("    PERS num a := -1;\n    PERS pos p := [1, 2, -3];"), []),
    (
        "persistent not literal",
        module("    CONST num c := 1;\n    PERS num a := c;"),
        ["not-literal"],
    ),
    ("non-value initialized", module("    VAR clock c := 1;"), ["value-class"]),
    ("initial value type", module('    VAR num a := "x";'), ["type-mismatch"]),
    ("array initial value size", module("    VAR num a{3} := [1, 2];"), ["aggregate-size"]),
    ("record initial value size", module("    VAR pos p := [1, 2];"), ["aggregate-size"]),
    ("aggregate for atomic", module("    VAR num a := [1];"), ["aggregate-type"]),
    ("record component type", module("    VAR pose p := [1, [1, 0, 0, 0]];"), ["type-mismatch"]),
    ("alias equal to its type", module("    VAR errnum e := 1;\n    VAR intnum i := 2;"), []),
    # --- 3 expressions
    ("undefined data object", proc("        a := 1;"), ["undefined-name"]),
    ("routine used as data", proc("        a := main;", "    VAR num a;"), ["not-a-data-object"]),
    ("operator types", proc('        a := 1 + "x";', "    VAR num a;"), ["operator-type"]),
    ("string concatenation", proc('        s := s + "x";', "    VAR string s;"), []),
    ("pos operators", proc("        p := p + p * 2;\n        p := -p;", "    VAR pos p;"), []),
    ("logical operator", proc("        b := 1 AND TRUE;", "    VAR bool b;"), ["operator-type"]),
    ("relational operator", proc('        b := "a" < "b";', "    VAR bool b;"), ["operator-type"]),
    (
        "equality of records",
        proc("        b := p = [1, 2, 3];", "    VAR bool b;\n    VAR pos p;"),
        [],
    ),
    (
        "aggregate without context",
        proc("        b := [1, 2] = [1, 2];", "    VAR bool b;"),
        ["aggregate-type"],
    ),
    ("not an array", proc("        a{1} := 1;", "    VAR num a;"), ["not-an-array"]),
    ("index count", proc("        a{1} := 1;", "    VAR num a{2, 2};"), ["index-count"]),
    (
        "index out of bounds",
        proc("        a{4} := 1;", "    VAR num a{3};"),
        ["index-out-of-bounds"],
    ),
    ("index type", proc('        a{"x"} := 1;', "    VAR num a{3};"), ["index-type"]),
    ("unknown component", proc("        p.w := 1;", "    VAR pos p;"), ["unknown-component"]),
    ("not a record", proc("        a.x := 1;", "    VAR num a;"), ["not-a-record"]),
    ("component of array element", proc("        p{2}.x := 1;", "    VAR pos p{2};"), []),
    ("undefined function", proc("        a := f(1);", "    VAR num a;"), ["undefined-routine"]),
    (
        "procedure used as function",
        proc("        a := main();", "    VAR num a;"),
        ["not-a-function"],
    ),
    # --- 4 statements
    ("assign constant", proc("        c := 2;", "    CONST num c := 1;"), ["assign-constant"]),
    (
        "assign loop variable",
        proc("        FOR i FROM 1 TO 3 DO\n            i := 2;\n        ENDFOR"),
        ["assign-readonly"],
    ),
    ("assign readonly ERRNO", proc("        ERRNO := 1;"), ["assign-readonly"]),
    ("assign non-value", proc("        c := c;", "    VAR clock c;"), ["value-class"]),
    ("assignment type", proc("        a := TRUE;", "    VAR num a;"), ["type-mismatch"]),
    (
        "condition type",
        proc(
            "        IF 1 THEN\n        ENDIF\n        WHILE a DO\n        ENDWHILE",
            "    VAR num a;",
        ),
        ["condition-type", "condition-type"],
    ),
    ("compact if", proc("        IF a > 1 a := 1;", "    VAR num a;"), []),
    ("for expression type", proc('        FOR i FROM "a" TO 3 DO\n        ENDFOR'), ["for-type"]),
    (
        "loop variable is num",
        proc("        FOR i FROM 1 TO 3 DO\n            a := i;\n        ENDFOR", "    VAR num a;"),
        [],
    ),
    (
        "test value type",
        proc(
            '        TEST a\n        CASE "x":\n            a := 1;\n        ENDTEST',
            "    VAR num a;",
        ),
        ["type-mismatch"],
    ),
    ("undefined label", proc("        GOTO nowhere;"), ["undefined-label"]),
    ("duplicate label", proc("        here:\n        here:"), ["duplicate-label"]),
    (
        "label and data object",
        module("    PROC p()\n        VAR num a;\n        a:\n    ENDPROC"),
        ["label-name-clash"],
    ),
    (
        "goto into a statement list",
        proc("        GOTO inside;\n        IF TRUE THEN\n            inside:\n        ENDIF"),
        ["goto-into-list"],
    ),
    (
        "goto out of a statement list",
        proc("        outside:\n        IF TRUE THEN\n            GOTO outside;\n        ENDIF"),
        [],
    ),
    ("return value in procedure", proc("        RETURN 1;"), ["return-value"]),
    (
        "return without value in function",
        module("    FUNC num f()\n        RETURN;\n    ENDFUNC"),
        ["missing-return", "return-value"],
    ),
    ("function without return", module("    FUNC num f()\n    ENDFUNC"), ["missing-return"]),
    (
        "return type",
        module('    FUNC num f()\n        RETURN "x";\n    ENDFUNC'),
        ["type-mismatch"],
    ),
    ("raise without number outside handler", proc("        RAISE;"), ["outside-error-handler"]),
    (
        "raise with number in handler",
        proc("        a := 1;\n    ERROR\n        RAISE 5;", "    VAR num a;"),
        ["raise-in-error-handler"],
    ),
    ("raise number range", proc("        RAISE 91;"), ["error-number"]),
    (
        "raise constant range",
        proc("        RAISE e;", "    CONST errnum e := 100;"),
        ["error-number"],
    ),
    ("retry outside handler", proc("        RETRY;"), ["outside-error-handler"]),
    ("trynext outside handler", proc("        TRYNEXT;"), ["outside-error-handler"]),
    (
        "error number list",
        proc("        a := 1;\n    ERROR (95, nothing)\n        RETRY;", "    VAR num a;"),
        ["error-number", "undefined-name"],
    ),
    (
        "connect",
        module(
            "    VAR intnum i;\n    PROC p()\n        CONNECT i WITH t;\n    ENDPROC\n    TRAP t\n    ENDTRAP"
        ),
        [],
    ),
    (
        "connect routine variable",
        module(
            "    PROC p()\n        VAR intnum i;\n        CONNECT i WITH t;\n    ENDPROC\n    TRAP t\n    ENDTRAP"
        ),
        ["connect-target"],
    ),
    (
        "connect to procedure",
        module("    VAR intnum i;\n    PROC p()\n        CONNECT i WITH p;\n    ENDPROC"),
        ["connect-trap"],
    ),
    # --- 4.6, 5 routine calls and parameters
    ("undefined procedure", proc("        nothing;"), ["undefined-routine"]),
    ("function used as procedure", proc("        Abs 1;"), ["not-a-procedure"]),
    (
        "trap call",
        module("    PROC p()\n        t;\n    ENDPROC\n    TRAP t\n    ENDTRAP"),
        ["trap-call"],
    ),
    ("too many arguments", proc("        main 1;"), ["argument-count"]),
    ("missing argument", proc("        TPWrite;"), ["missing-argument"]),
    ("argument type", proc("        TPWrite 1;"), ["type-mismatch"]),
    (
        "named argument",
        proc('        TPWrite String := "a";\n        TPWrite Str := "a";'),
        ["argument-name"],
    ),
    (
        "unknown optional argument",
        proc('        TPWrite "a" \\Nothing := 1;'),
        ["unknown-argument"],
    ),
    (
        "required written as optional",
        proc('        TPWrite \\String := "a";'),
        ["argument-name", "missing-argument"],
    ),
    (
        "exclusive arguments",
        proc('        TPWrite "a" \\Num := 1 \\Bool := TRUE;'),
        ["exclusive-arguments"],
    ),
    ("optional argument value", proc('        TPWrite "a" \\Num;'), ["missing-argument-value"]),
    ("switch argument value", proc("        WaitTime \\InPos := 1, 1;"), ["switch-value"]),
    (
        "argument order",
        module(
            "    PROC q(\\num a, \\num b)\n    ENDPROC\n    PROC p()\n        q \\b := 1 \\a := 2;\n    ENDPROC"
        ),
        ["argument-order"],
    ),
    (
        "conditional argument",
        proc('        TPWrite "a" \\Num ? x;', "    VAR num x;"),
        ["conditional-argument"],
    ),
    ("var argument expression", proc("        Incr 1;"), ["argument-mode"]),
    ("var argument constant", proc("        Incr c;", "    CONST num c := 1;"), ["argument-mode"]),
    (
        "var argument loop variable",
        proc("        FOR i FROM 1 TO 2 DO\n            Incr i;\n        ENDFOR"),
        ["argument-mode"],
    ),
    (
        "var argument variable",
        proc("        Incr a;\n        Incr b{1};", "    VAR num a;\n    VAR num b{2};"),
        [],
    ),
    (
        "pers argument variable",
        module(
            "    VAR num a;\n    PROC q(PERS num x)\n    ENDPROC\n    PROC p()\n        q a;\n    ENDPROC"
        ),
        ["argument-mode"],
    ),
    (
        "pers argument persistent",
        module(
            "    PERS num a := 1;\n    PROC q(PERS num x)\n    ENDPROC\n    PROC p()\n        q a;\n    ENDPROC"
        ),
        [],
    ),
    (
        "array argument",
        module(
            "    VAR num a{3};\n    PROC q(num x{*})\n    ENDPROC\n    PROC p()\n        q a;\n        q a{1};\n    ENDPROC"
        ),
        ["type-mismatch"],
    ),
    ("switch not optional", module("    PROC q(switch s)\n    ENDPROC"), ["switch-not-optional"]),
    ("non-value in parameter", module("    PROC q(clock c)\n    ENDPROC"), ["value-class"]),
    ("non-value var parameter", module("    PROC q(VAR clock c)\n    ENDPROC"), []),
    (
        "non-value function",
        module("    FUNC clock f()\n        RETURN c;\n    ENDFUNC\n    VAR clock c;"),
        ["value-class"],
    ),
    ("present", proc("        IF Present(a) THEN\n        ENDIF", "", "\\num a"), []),
    (
        "present required parameter",
        proc("        IF Present(a) THEN\n        ENDIF", "", "num a"),
        ["present-argument"],
    ),
    ("dim", proc("        x := Dim(a, 1);", "    VAR num a{3};\n    VAR num x;"), []),
]


@pytest.mark.parametrize("text, expected", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_rule(text: str, expected: list[str]) -> None:
    assert codes(text) == sorted(expected), "\n".join(str(d) for d in diagnostics(text))


# test files of the parser that are not valid RAPID: (line, code) expected
INVALID_FILES = {
    "rapid1.mod": [
        (85, "duplicate-name"),  # PROC PIPPO and ALIAS num pippo (case insensitive)
        (116, "undefined-name"),
        (149, "present-argument"),
        (171, "not-a-procedure"),
        (200, "not-a-procedure"),
    ],
    "test1.mod": [(5, "unknown-type")],
    "test6.mod": [(9, "duplicate-name")],
    "test7.mod": [(9, "duplicate-name")],
    "test8.mod": [
        (10, "not-constant"),  # VAR initialized with variables
        (11, "not-constant"),
        (12, "not-constant"),
        (12, "not-constant"),
        (13, "not-constant"),  # function calls, func is not declared
        (13, "undefined-routine"),
        (14, "not-constant"),
        (14, "undefined-routine"),
        (15, "not-constant"),
        (15, "undefined-routine"),
        (16, "duplicate-name"),  # p7 declared twice
        (16, "not-constant"),
        (16, "undefined-routine"),
        (17, "not-constant"),
        (17, "undefined-routine"),
        (18, "not-constant"),
        (18, "undefined-routine"),
        (19, "not-constant"),
        (19, "undefined-name"),
        (19, "undefined-routine"),
        (21, "missing-value"),  # CONST without value
        (28, "argument-count"),  # ppippo has no parameters
    ],
    "test10.mod": [(2, "aggregate-size"), (2, "type-mismatch"), (2, "type-mismatch")],
    "test15.mod": [(3, "undefined-name")],
    "test17.mod": [(3, "undefined-name")],
    "test18.mod": [(3, "undefined-name")],
    "test20.mod": [(2, "duplicate-global")],
    "test30.mod": [(6, "not-literal")],
    "test33.mod": [(17, "local-in-routine")],
    "test40.mod": [(8, "not-literal")],
}

ALL_FILES = sorted(
    os.path.basename(f)
    for f in os.listdir(TEST_DIR)
    if f.endswith(".mod") and not f.endswith((".ast.mod", ".source.mod", "rapid_program.mod"))
)


@pytest.mark.parametrize("name", ALL_FILES)
def test_file(name: str) -> None:
    path = os.path.join(TEST_DIR, name)
    found = [
        (d.line, d.code)
        for d in rapidvalidate.validate_files([path])
        if d.severity == rapidvalidate.ERROR
    ]
    assert sorted(found) == sorted(INVALID_FILES.get(name, []))


def test_standard_modules() -> None:
    """default/*.sys must be valid RAPID: they are loaded with every program"""
    found = rapidvalidate.validate(standard_modules())
    assert found == [], "\n".join(str(d) for d in found)


def test_command_line(capsys: pytest.CaptureFixture[str]) -> None:
    assert rapidvalidate.main([os.path.join(TEST_DIR, "test2.mod")]) == 0
    assert rapidvalidate.main([os.path.join(TEST_DIR, "test6.mod")]) == 1
    out = capsys.readouterr().out
    assert "test6.mod:9: error: 'pippo' is already declared" in out
    assert out.rstrip().endswith("[duplicate-name]")
