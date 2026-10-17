"""String literals (RAPID kernel manual, 2.7):

    <string literal> ::= '"' { <character> | <character code> } '"'
    <character code> ::= '\\' <hex digit> <hex digit>

"If a back slash or double quote character should be included in a string literal
it must be written twice."
"""

from typing import Any

import pytest

import rapid_parser
from plyparser import ParseError
from rapid_lexer import decode_string

PARSER = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)

CASES = [
    ('"A string literal"', "A string literal", "A string literal"),
    ('"Contains a "" character"', 'Contains a "" character', 'Contains a " character'),
    (
        '"Ends with BEL control character\\07"',
        "Ends with BEL control character\\07",
        "Ends with BEL control character\x07",
    ),
    ('"Contains a \\\\ character"', "Contains a \\\\ character", "Contains a \\ character"),
    ('""', "", ""),
    ('"x\\41y"', "x\\41y", "xAy"),
]


def literal(text: str) -> Any:
    module = PARSER.parse("MODULE m\n    VAR string s := %s;\nENDMODULE\n" % (text,), "strings")
    return module.data_definitions[0].definition.variable_instance.value.expression.expr.value


@pytest.mark.parametrize("text, raw, value", CASES, ids=[c[0] for c in CASES])
def test_string_literal(text: str, raw: str, value: str) -> None:
    assert literal(text) == raw
    assert decode_string(raw) == value


# a back slash that is not doubled and does not start a character code \hh
INVALID = [r'"a\nb"', r'"C:\"', r'"\4"', r'"WaitTime \InPos"']


@pytest.mark.parametrize("text", INVALID, ids=["newline", "at the end", "one digit", "letter"])
def test_invalid_back_slash(text: str) -> None:
    with pytest.raises(ParseError):
        literal(text)
