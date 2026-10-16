"""Round-trip test: .mod -> AST -> rapid2rapid -> .mod -> AST -> rapid2rapid.

The text produced by the first and the second conversion must be identical.
"""
import glob
import io
import os

import pytest

import rapid_ast
import rapid_parser
from rapid2rapid import WriteRapid

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test")
# *.ast.mod / *.source.mod are outputs of test_rapid.py
MOD_FILES = sorted(
    f for f in glob.glob(os.path.join(TEST_DIR, "*.mod"))
    if not f.endswith((".ast.mod", ".source.mod", "rapid_program.mod"))
)


def convert(text, filename):
    parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False,
                                      start_from='module_declaration_list')
    modules = rapid_ast.ModulesAST(parser.parse(text, filename, debuglevel=0).module_list)
    out = io.StringIO()
    WriteRapid(filew=out).visit(modules)
    return out.getvalue()


@pytest.mark.parametrize("path", MOD_FILES, ids=os.path.basename)
def test_rapid2rapid_roundtrip(path):
    with open(path, "r") as f:
        source = f.read()

    first = convert(source, path)
    assert first.strip(), "conversion produced no output"

    second = convert(first, path + " (reconverted)")
    assert first == second
