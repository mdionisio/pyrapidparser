"""RAPID overview manual 1.1.1: "The language is not case sensitive, for example upper
case and lower case letters are considered the same." Keywords included."""

import pytest

import rapid_parser
from plyparser import ParseError

PARSER = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)

LOWER_CASE = """module lower(sysmodule)
    var num a := 7 div 2;
    proc main(\\switch on, var num x)
        if not a = 4 and true then
            x := a;
        elseif a > 3 or true then
            x := 0;
        endif
        for i from 1 to 2 do
            x := x + i;
        endfor
    error
        retry;
    endproc
endmodule
"""


def test_lower_case_keywords() -> None:
    module = PARSER.parse(LOWER_CASE, "lower")
    assert [a.name for a in module.module_attribute] == ["SYSMODULE"]
    proc = module.routine_definitions[0].definition
    assert proc.parameter_list[1].parameter_type == "VAR"
    expr = module.data_definitions[0].definition.variable_instance.value.expression.expr
    assert expr.operator == "DIV"
    assert proc.routine_error is not None


@pytest.mark.parametrize("name", ["test", "Test", "PROC", "Func", "endmodule"])
def test_reserved_word_is_not_an_identifier(name: str) -> None:
    with pytest.raises(ParseError):
        PARSER.parse("MODULE m\n    VAR num %s;\nENDMODULE\n" % (name,), "reserved")
