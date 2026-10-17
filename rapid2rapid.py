#!/usr/bin/env python3
from typing import Any, TextIO

from browse_rapid_ast import ensure_dir
import rapid_ast
import rapid_parser
import os
import os.path


class WriteRapid(rapid_ast.NodeVisitor):
    __indent__ = "\t"

    def __init__(self, filew: TextIO) -> None:
        self.file = filew
        self.indent = 0

    def writeindent(self) -> None:
        self.file.write(WriteRapid.__indent__ * self.indent)

    def write(self, data: str = "\n") -> None:
        self.file.write(data)

    def writeln(self, data: str) -> None:
        self.writeindent()
        self.write(data)
        self.write()

    def write_list(self, items: list[Any], separator: str = ", ") -> None:
        for n, i in enumerate(items):
            if n > 0:
                self.write(separator)
            self.visit(i)

    def write_arguments(self, arguments: list[Any]) -> None:
        # required arguments are comma separated, optional/conditional ones
        # (introduced by a backslash) just follow the previous argument
        for n, i in enumerate(arguments):
            if n > 0:
                self.write(", " if i.type == "Required" else " ")
            self.visit(i)

    def visit_FunctionArgumentAST(self, node: rapid_ast.FunctionArgumentAST) -> None:
        # type, argumentname*, argumentvalue*
        if node.type == "Optional":
            self.write("\\")
            self.visit(node.argumentname)
            if not (node.argumentvalue is None):
                self.write(" := ")
                self.visit(node.argumentvalue)
        elif node.type == "Conditional":
            self.write("\\")
            self.visit(node.argumentname)
            self.write(" ? ")
            self.visit(node.argumentvalue)
        else:
            if not (node.argumentname is None):
                self.visit(node.argumentname)
                self.write(" := ")
            self.visit(node.argumentvalue)

    visit_ProcedureArgumentAST = visit_FunctionArgumentAST

    def visit_FunctionCallAST(self, node: rapid_ast.FunctionCallAST) -> None:
        self.visit(node.function)
        self.write("(")
        self.write_arguments(node.arguments)
        self.write(")")

    def visit_ProcedureCallAST(self, node: rapid_ast.ProcedureCallAST, **kwargs: Any) -> None:
        # procedure is IdentifierAST or ExpressionAST
        # arguments list of ProcedureArgumentAST
        self.writeindent()
        self.visit(node.procedure)
        if len(node.arguments) > 0:
            self.write(" ")
            self.write_arguments(node.arguments)
        self.write(";")
        self.write()

    def visit_VariableAST(self, node: rapid_ast.VariableAST) -> None:
        if (node.var is None) and (len(node.index) == 0) and (node.component is None):
            self.write("<VAR>")
        elif (len(node.index) == 0) and (node.component is None):
            self.visit(node.var)
        elif node.component is None:
            self.visit(node.var)
            self.write("{")
            self.write_list(node.index)
            self.write("}")
        else:
            self.visit(node.var)
            self.write(".")
            self.visit(node.component)

    def visit_AggregateAST(self, node: rapid_ast.AggregateAST) -> None:
        self.write("[")
        self.write_list(node.expr)
        self.write("]")

    def visit_Operator1AST(self, node: rapid_ast.Operator1AST) -> None:
        if not (node.operator is None):
            self.write(node.operator)
            self.write(" ")
        self.visit(node.par1)

    def visit_Operator2AST(self, node: rapid_ast.Operator2AST) -> None:
        self.visit(node.par1)
        self.write(" ")
        self.write(node.operator)
        self.write(" ")
        self.visit(node.par2)

    def visit_LiteralATS(self, node: rapid_ast.LiteralATS) -> None:
        if isinstance(node.value, str):
            self.write('"%s"' % (node.value,))
        else:
            self.write("%s" % (str(node.value),))

    def visit_ExpressionAST(self, node: rapid_ast.ExpressionAST) -> None:
        if not (node.expr is None):
            self.visit(node.expr)

    def visit_IdentifierAST(self, node: rapid_ast.IdentifierAST) -> None:
        if node.name is None:
            self.write("<ID>")
        else:
            self.write(node.name)

    def visit_CommentAST(self, node: rapid_ast.CommentAST) -> None:
        self.writeln("!" + node.comment)

    def visit_ModuleAST(self, node: rapid_ast.ModuleAST) -> None:
        # module_name*, module_attribute**, type_definitions**, data_definitions**, routine_definitions**
        self.writeindent()
        self.write("MODULE ")
        self.visit(node.module_name)
        self.write(" ")
        if len(node.module_attribute) > 0:
            self.write("(")
            for i in node.module_attribute[:-1]:
                self.write(i.name)
                self.write(", ")
            self.write(node.module_attribute[-1].name)
            self.write(")")
        self.write()
        self.indent += 1
        for i in node.type_definitions:
            self.visit(i)
        for i in node.data_definitions:
            self.visit(i)
        for i in node.routine_definitions:
            self.visit(i)
        self.indent -= 1
        self.writeln("ENDMODULE")

    def visit_VarDefinitionAST(self, node: rapid_ast.VarDefinitionAST) -> None:
        self.visit(node.name)
        if len(node.size) > 0:
            self.write("{")
            self.write_list(node.size)
            self.write("}")
        if not (node.value is None):
            self.write(" := ")
            self.visit(node.value)

    def visit_VarDeclarationAST(self, node: rapid_ast.VarDeclarationAST) -> None:
        self.write("VAR ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
        self.write(";")

    def visit_PersDeclarationAST(self, node: rapid_ast.PersDeclarationAST) -> None:
        self.write("PERS ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
        self.write(";")

    def visit_ConstDeclarationAST(self, node: rapid_ast.ConstDeclarationAST) -> None:
        self.write("CONST ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
        self.write(";")

    def visit_DataDefATS(self, node: rapid_ast.DataDefATS) -> None:
        self.writeindent()
        if not (node.type is None):
            self.write(node.type + " ")
        if node.definition is None:
            self.write("<DDN>")
        else:
            self.visit(node.definition)
        self.write()

    def visit_TypeDefAST(self, node: rapid_ast.TypeDefAST) -> None:
        self.writeindent()
        if not (node.type is None):
            self.write(node.type + " ")

        if node.definition is None:
            self.write("<TDN>")
        else:
            self.visit(node.definition)
        self.write()

    def visit_AliasDefATS(self, node: rapid_ast.AliasDefATS) -> None:
        self.write("ALIAS ")
        self.visit(node.type_name)
        self.write(" ")
        self.visit(node.alias_name)
        self.write(";")

    def visit_RecordDefAST(self, node: rapid_ast.RecordDefAST) -> None:
        self.write("RECORD ")
        self.visit(node.record_name)
        self.write()
        self.indent += 1
        for i in node.components:
            self.visit(i)
        self.indent -= 1
        self.writeindent()
        self.write("ENDRECORD")

    def visit_RecordComponentDefAST(self, node: rapid_ast.RecordComponentDefAST) -> None:
        self.writeindent()
        self.visit(node.data_type)
        self.write(" ")
        self.visit(node.record_component_name)
        self.write(";")
        self.write()

    def visit_RoutineDeclarationATS(self, node: rapid_ast.RoutineDeclarationATS) -> None:
        self.writeindent()
        if not (node.type is None):
            self.write(node.type + " ")
        if node.definition is None:
            self.write("<RDN>")
        else:
            self.visit(node.definition)
        self.write()

    def visit_ParameterDefinitionAST(self, node: rapid_ast.ParameterDefinitionAST) -> None:
        # parameter_type, type*, name*, size
        if node.parameter_type != "NORMAL":
            self.write(node.parameter_type)
            self.write(" ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.name)
        if node.size is None:
            self.write("{<DIM>}")
        elif node.size > 0:
            self.write("{" + ", ".join(["*"] * node.size) + "}")

    def visit_SwitchParameterDefinitionAST(
        self, node: rapid_ast.SwitchParameterDefinitionAST
    ) -> None:
        self.write("switch ")
        self.visit(node.name)

    def visit_OptionalParameterDefinitionAST(
        self, node: rapid_ast.OptionalParameterDefinitionAST
    ) -> None:
        # parameter*, switchs**
        self.write("\\")
        if node.parameter is None:
            self.write("<ALT>")
        else:
            self.visit(node.parameter)
        for i in node.switchs:
            self.write(" | ")
            if i is None:
                self.write("<ALT>")
            else:
                self.visit(i)

    def write_parameters(self, parameter_list: list[Any]) -> None:
        for n, i in enumerate(parameter_list):
            if n > 0:
                self.write(", ")
            if i is None:
                self.write("<PAR>")
            else:
                self.visit(i)

    def visit_ProcedureDeclarationAST(self, node: rapid_ast.ProcedureDeclarationAST) -> None:
        self.write("PROC ")
        self.visit(node.procedure_name)
        self.write(" (")
        self.write_parameters(node.parameter_list)
        self.write(")")
        self.write()

        self.indent += 1

        for i in node.data_definitions:
            self.visit(i)

        for i in node.statement_list:
            self.visit(i)

        if not (node.routine_backward is None):
            self.visit(node.routine_backward)

        if not (node.routine_error is None):
            self.visit(node.routine_error)

        if not (node.routine_undo is None):
            self.visit(node.routine_undo)

        self.indent -= 1
        self.writeindent()
        self.write("ENDPROC")

    def visit_FunctionDeclarationAST(self, node: rapid_ast.FunctionDeclarationAST) -> None:
        # data_type*, function_name*, parameter_list**, data_definitions**, statement_list**, routine_error*, routine_undo*
        self.write("FUNC ")
        self.visit(node.data_type)
        self.write(" ")
        self.visit(node.function_name)
        self.write(" (")
        self.write_parameters(node.parameter_list)
        self.write(")")
        self.write()

        self.indent += 1

        for i in node.data_definitions:
            self.visit(i)

        for i in node.statement_list:
            self.visit(i)

        if not (node.routine_error is None):
            self.visit(node.routine_error)

        if not (node.routine_undo is None):
            self.visit(node.routine_undo)

        self.indent -= 1
        self.writeindent()
        self.write("ENDFUNC")

    def visit_TrapDeclarationAST(self, node: rapid_ast.TrapDeclarationAST) -> None:
        # procedure_name*, data_definitions**, statement_list**, routine_error*, routine_undo*
        self.write("TRAP ")
        self.visit(node.procedure_name)
        self.write()

        self.indent += 1

        for i in node.data_definitions:
            self.visit(i)

        for i in node.statement_list:
            self.visit(i)

        if not (node.routine_error is None):
            self.visit(node.routine_error)

        if not (node.routine_undo is None):
            self.visit(node.routine_undo)

        self.indent -= 1
        self.writeindent()
        self.write("ENDTRAP")

    def write_routine_section(self, keyword: str, statement_list: list[Any]) -> None:
        self.writeindent()
        self.write(keyword)
        self.write()
        self.indent += 1
        for i in statement_list:
            self.visit(i)
        self.indent -= 1

    def visit_RoutineBackwardAST(self, node: rapid_ast.RoutineBackwardAST) -> None:
        self.write_routine_section("BACKWARD", node.statement_list)

    def visit_RoutineUndoAST(self, node: rapid_ast.RoutineUndoAST) -> None:
        self.write_routine_section("UNDO", node.statement_list)

    def visit_RoutineErrorAST(self, node: rapid_ast.RoutineErrorAST) -> None:
        keyword = "ERROR"
        if len(node.error_number_list) > 0:
            keyword += (
                " ("
                + ", ".join(
                    str(getattr(i, "name", None) or getattr(i, "value", i))
                    for i in node.error_number_list
                )
                + ")"
            )
        self.write_routine_section(keyword, node.statement_list)

    def visit_LabelAST(self, node: rapid_ast.LabelAST) -> None:
        self.writeindent()
        self.visit(node.name)
        self.write(":")
        self.write()

    def visit_AssignmentStatementAST(self, node: rapid_ast.AssignmentStatementAST) -> None:
        # dest*, source*
        self.writeindent()
        self.visit(node.dest)
        self.write(" := ")
        self.visit(node.source)
        self.write(";")
        self.write()

    def visit_GotoStatementAST(self, node: rapid_ast.GotoStatementAST) -> None:
        # dest*
        self.writeindent()
        self.write("GOTO ")
        self.visit(node.dest)
        self.write(";")
        self.write()

    def visit_ReturnStatementAST(self, node: rapid_ast.ReturnStatementAST) -> None:
        # result*
        self.writeindent()
        self.write("RETURN ")
        if not (node.result is None):
            self.visit(node.result)
        self.write(";")
        self.write()

    def visit_RaiseStatementAST(self, node: rapid_ast.RaiseStatementAST) -> None:
        # error_number*
        self.writeindent()
        self.write("RAISE ")
        if not (node.error_number is None):
            self.visit(node.error_number)
        self.write(";")
        self.write()

    def visit_ExitStatementAST(self, node: rapid_ast.ExitStatementAST) -> None:
        self.writeindent()
        self.write("EXIT ;")
        self.write()

    def visit_RetryStatementAST(self, node: rapid_ast.RetryStatementAST) -> None:
        self.writeindent()
        self.write("RETRY ;")
        self.write()

    def visit_TrynextStatementAST(self, node: rapid_ast.TrynextStatementAST) -> None:
        self.writeindent()
        self.write("TRYNEXT ;")
        self.write()

    def visit_ConnectStatementAST(self, node: rapid_ast.ConnectStatementAST) -> None:
        # connect_taget*, trap*
        self.writeindent()
        self.write("CONNECT ")
        self.visit(node.connect_taget)
        self.write(" WITH ")
        self.visit(node.trap)
        self.write(";")
        self.write()

    def visit_IfStatement(self, node: rapid_ast.IfStatement) -> None:
        # condition*, statement_list**, elseif_list**, else_statement_list**
        self.writeindent()
        self.write("IF ")
        self.visit(node.condition)
        self.write(" THEN")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        if len(node.elseif_list) > 0:
            for i in node.elseif_list:
                self.visit(i)
        if len(node.else_statement_list) > 0:
            self.writeindent()
            self.write("ELSE")
            self.write()
            self.indent += 1
            for i in node.else_statement_list:
                self.visit(i)
            self.indent -= 1
        self.writeindent()
        self.write("ENDIF")
        self.write()

    def visit_ElseIfStatement(self, node: rapid_ast.ElseIfStatement) -> None:
        # condition*, statement_list**
        self.writeindent()
        self.write("ELSEIF ")
        self.visit(node.condition)
        self.write(" THEN")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1

    def visit_ForStatement(self, node: rapid_ast.ForStatement) -> None:
        # loop_variable*, ifrom*, ito*, istep*, statement_list**
        self.writeindent()
        self.write("FOR ")
        self.visit(node.loop_variable)
        self.write(" FROM ")
        self.visit(node.ifrom)
        self.write(" TO ")
        self.visit(node.ito)
        if not (node.istep is None):
            self.write(" STEP ")
            self.visit(node.istep)
        self.write(" DO")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        self.writeindent()
        self.write("ENDFOR")
        self.write()

    def visit_WhileStatement(self, node: rapid_ast.WhileStatement) -> None:
        # condition*, statement_list**
        self.writeindent()
        self.write("WHILE ")
        self.visit(node.condition)
        self.write(" DO")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        self.writeindent()
        self.write("ENDWHILE")
        self.write()

    def visit_TestStatement(self, node: rapid_ast.TestStatement) -> None:
        # expression*, cases**, default**
        self.writeindent()
        self.write("TEST ")
        self.visit(node.expression)
        self.write()
        for i in node.cases:
            self.visit(i)
        if len(node.default) > 0:
            self.writeindent()
            self.write("DEFAULT:")
            self.write()
            self.indent += 1
            for i in node.default:
                self.visit(i)
            self.indent -= 1
        self.writeindent()
        self.write("ENDTEST")
        self.write()

    def visit_CaseStatement(self, node: rapid_ast.CaseStatement) -> None:
        # test_value*, statement_list**
        self.writeindent()
        if node.test_value is None:
            self.write("<CSE>")
            self.write()
        else:
            self.write("CASE ")
            for n, v in enumerate(node.test_value):
                if n > 0:
                    self.write(", ")
                self.visit(v)
            self.write(" : ")
            self.write()
            self.indent += 1
            for i in node.statement_list:
                self.visit(i)
            self.indent -= 1


if __name__ == "__main__":
    import sys

    from optparse import OptionParser

    optparser = OptionParser()
    optparser.add_option(
        "-f",
        "--file",
        action="store",
        type="string",
        dest="filename",
        default="rapid_program.mod",
        help="output filename",
        metavar="FILE",
    )
    optparser.add_option(
        "-d",
        "--directory",
        action="store",
        type="string",
        dest="directory",
        default="test",
        help="output directory",
        metavar="DIRECTORY",
    )

    optparser.add_option(
        "-i",
        "--infile",
        action="store",
        type="string",
        dest="infiles",
        help="input file to convert",
        metavar="FILE",
    )

    (options, args) = optparser.parse_args()

    text = ""
    filename = ""
    if not (options.infiles is None):
        filename = options.infiles
        with open(filename, "r") as f:
            text = f.read()

    parser = rapid_parser.RAPIDParser(
        lex_optimize=True,
        yacc_debug=False,
        yacc_optimize=False,
        start_from="module_declaration_list",
    )
    attriblist = parser.parse(text, filename, debuglevel=0).module_list

    allmodule = rapid_ast.ModulesAST(attriblist)

    filename = os.path.join(options.directory, options.filename)
    with open(filename, "w+t") as f:
        traslate = WriteRapid(filew=f)
        traslate.visit(allmodule)
