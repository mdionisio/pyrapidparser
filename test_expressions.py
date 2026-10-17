"""Expression trees: operator priority and left to right evaluation.

RAPID kernel manual, 3.1 Introduction to expressions:
    <expr>         ::= [ NOT ] <logical term> { ( OR | XOR ) <logical term> }
    <logical term> ::= <relation> { AND <relation> }
    <relation>     ::= <simple expr> [ <relop> <simple expr> ]
    <simple expr>  ::= [ <addop> ] <term> { <addop> <term> }
    <term>         ::= <primary> { <mulop> <primary> }
"Operators of the same priority are evaluated from left to right."
"""

import io
from typing import Any

import pytest

import rapid_ast
import rapid_parser
from rapid2rapid import WriteRapid

PARSER = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)


def parse_expression(text: str) -> Any:
    module = PARSER.parse(
        "MODULE m\n    PROC main()\n        r := %s;\n    ENDPROC\nENDMODULE\n" % (text,), "expr"
    )
    statement = module.routine_definitions[0].definition.statement_list[0].statement
    return statement.source


def tree(node: Any) -> str:
    """the expression with every operator in parentheses"""
    if isinstance(node, rapid_ast.ExpressionAST):
        return tree(node.expr)
    if isinstance(node, rapid_ast.Operator2AST):
        return "(%s %s %s)" % (tree(node.par1), node.operator, tree(node.par2))
    if isinstance(node, rapid_ast.Operator1AST):
        sep = " " if node.operator == "NOT" else ""
        return "(%s%s%s)" % (node.operator, sep, tree(node.par1))
    if isinstance(node, rapid_ast.VariableAST):
        return str(node.var.name)
    if isinstance(node, rapid_ast.LiteralATS):
        return str(node.value)
    raise AssertionError("unexpected node %r" % (node,))


def rewrite(node: Any) -> str:
    out = io.StringIO()
    WriteRapid(filew=out).visit(node)
    return out.getvalue()


CASES = [
    ("a - b - c", "((a - b) - c)"),
    ("a - b + c", "((a - b) + c)"),
    ("a / b / c", "((a / b) / c)"),
    ("a DIV b * c", "((a DIV b) * c)"),
    ("a + b * c", "(a + (b * c))"),
    ("a * (b + c)", "(a * (b + c))"),
    ("a - (b - c)", "(a - (b - c))"),
    ("-a + b", "((-a) + b)"),
    ("-a * b", "(-(a * b))"),
    ("a * (-b)", "(a * (-b))"),
    ("a < -b", "(a < (-b))"),
    ("(a < b) = c", "((a < b) = c)"),
    ("a < b AND c < d", "((a < b) AND (c < d))"),
    ("a AND b AND c", "((a AND b) AND c)"),
    ("a OR b XOR c", "((a OR b) XOR c)"),
    ("a OR b AND c", "(a OR (b AND c))"),
    ("NOT a OR b", "((NOT a) OR b)"),
    ("NOT a AND b", "(NOT (a AND b))"),
    ("NOT (a OR b)", "(NOT (a OR b))"),
    ("a OR (NOT b)", "(a OR (NOT b))"),
]


@pytest.mark.parametrize("text, expected", CASES, ids=[c[0] for c in CASES])
def test_expression_tree(text: str, expected: str) -> None:
    assert tree(parse_expression(text)) == expected


@pytest.mark.parametrize("text, expected", CASES, ids=[c[0] for c in CASES])
def test_rapid2rapid_keeps_expression_tree(text: str, expected: str) -> None:
    written = rewrite(parse_expression(text))
    assert tree(parse_expression(written)) == expected, written
