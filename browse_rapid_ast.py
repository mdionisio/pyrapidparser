import rapid_ast
import os
import os.path
import run.pyrapid as pyrapid
import copy

def ensure_dir(f):
    d = os.path.dirname(f)
    if len(d)==0:
        d = f
    if not os.path.exists(d):
        os.makedirs(d)

class WriteRapid( rapid_ast.NodeVisitor ):
    __indent__ = '\t'
    def __init__(self, filew):
        self.file = filew
        self.indent=0
        
    def writeindent(self):
        self.file.write(WriteRapid.__indent__*self.indent)
        
    def write(self, data="\n"):
        self.file.write(data)
        
    def writeln(self, data):
        self.writeindent()
        self.write(data)
        self.write()
        
    def visit_FunctionCallAST(self, node):
        self.visit(node.function)
        self.write("(")
        if len(node.arguments)>0:
            for i in node.arguments[:-1]:
                self.visit(i)
            self.visit(node.arguments[-1])
        self.write(")")
        
    def visit_VariableAST(self, node):
        if (node.var is None) and (len(node.index)==0) and (node.component is None):
            self.write("<VAR>")
        elif  (len(node.index)==0) and (node.component is None):
            self.visit(node.var)
        elif  (node.component is None):
            self.visit(node.var)
            self.write("{")
            for i in node.index:
                self.write(i)
                self.write(", ")
            self.write(node.index[-1])
            self.write("}")
        else:
            self.visit(node.var)
            self.write(".")
            self.visit(node.component)
            
        
    def visit_AggregateAST(self, node):
        self.write("[")
        if len(node.expr)>0:
            for i in node.expr[:-1]:
                self.visit(i)
                self.write(", ")
            self.visit(node.expr[-1])
        self.write("]")
        
    def visit_Operator1AST(self, node):
        if not(node.operator is None):
            self.write(node.operator)
            self.write(" ")
        self.visit(node.par1)
        
    def visit_Operator2AST(self, node):
        self.visit(node.par1)
        self.write(" ")
        self.write(node.operator)
        self.write(" ")
        self.visit(node.par2)
        
    def visit_LiteralATS(self, node):
        self.write("%s"%(node.value,))
        
    def visit_ExpressionAST(self, node):        
        if not(node.expr is None):
            self.visit(node.expr)
        
    def visit_IdentifierAST(self, node):        
        if node.name is None:
            self.write("<ID>")
        else:
            self.write(node.name)
    
    def visit_CommentAST(self, node):        
        self.writeln("!"+node.comment)
        
    def visit_ModuleAST(self, node):
        #module_name*, module_attribute**, type_definitions**, data_definitions**, routine_definitions**
        self.writeindent()
        self.write("MODULE ")
        self.visit(node.module_name)
        self.write(" ")
        if len(node.module_attribute)>0:
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
        
    def visit_VarDefinitionAST(self, node):     
        self.visit(node.name)
        if len(node.size)>0:
            self.write("[")
            for i in node.size[:-1]:
                self.visit(i)
                self.write(", ")
            self.visit(node.size[-1])
            self.write("]")
        if not (node.value is None):
            self.write(" := ")
            self.visit(node.value)
        
    def visit_VarDeclarationAST(self, node):     
        self.write("VAR ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
        
    def visit_PersDeclarationAST(self, node):     
        self.write("PERS ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
        
    def visit_ConstDeclarationAST(self, node):     
        self.write("CONST ")
        self.visit(node.type)
        self.write(" ")
        self.visit(node.variable_instance)
    
    def visit_DataDefATS(self, node):     
        self.writeindent()
        if not(node.type is None):
            self.write(node.type + " ")
        if node.definition is None:
            self.write("<DDN>") 
        else:
            self.visit(node.definition)
        self.write() 
        
    def visit_TypeDefAST(self, node):     
        self.writeindent()
        if not(node.type is None):
            self.write(node.type + " ")
        
        if node.definition is None:
            self.write("<TDN>")
        else:
            self.visit(node.definition)
        self.write() 
        
    def visit_AliasDefATS(self, node):     
        self.write("ALIAS ") 
        self.visit(node.type_name)
        self.write(" ") 
        self.visit(node.alias_name)
        self.write(";") 
        
    def visit_RecordDefAST(self, node):     
        self.write("RECORD ") 
        self.visit(node.record_name)
        self.write() 
        self.indent += 1
        for i in node.components:
            self.visit(i)
        self.indent -= 1
        self.writeindent()
        self.write("ENDRECORD") 
        
    def visit_RecordComponentDefAST(self, node):     
        self.writeindent()
        self.write("RECORD ") 
        self.visit(node.data_type)
        self.write(" ") 
        self.visit(node.record_component_name)
        self.write() 
        
    def visit_RoutineDeclarationATS(self, node):
        self.writeindent()
        if not(node.type is None):
            self.write(node.type + " ")
        if node.definition is None:
            self.write("<RDN>") 
        else:
            self.visit(node.definition)
        self.write() 
        
    def visit_ParameterDefinitionAST(self, node):
        #parameter_type, type*, name*, size
        if node.size is None:
            pass
        elif node.size == 0:
            self.write(node.parameter_type)
            self.write(" ")
            self.visit(node.type)
            self.write(" ")
            self.visit(node.name)
        else:
            pass
        
    def visit_ProcedureDeclarationAST(self, node):
        self.write("PROC ")
        self.visit(node.procedure_name)
        self.write(" (")
        if len(node.parameter_list)>0:
            for i in node.parameter_list[:-1]:
                if i is None:
                    self.write("<PAR>")
                else:
                    self.visit(i)
                self.write(", ")
            if node.parameter_list[-1] is None:
                self.write("<PAR>")
            else:
                self.visit(node.parameter_list[-1])
        self.write(")")
        self.write()
        
        self.indent += 1
        
        for i in node.data_definitions:
            self.visit(i)
            
        for i in node.statement_list:
            self.visit(i)
            
        if not(node.routine_backward is None):
            self.visit(node.routine_backward)
            
        if not(node.routine_error is None):
            self.visit(node.routine_error)
        
        if not(node.routine_undo is None):
            self.visit(node.routine_undo)
            
        self.indent -= 1
        self.writeindent()
        self.write("ENDPROC") 
        
    def visit_FunctionDeclarationAST(self, node):
        #data_type*, function_name*, parameter_list**, data_definitions**, statement_list**, routine_error*, routine_undo*
        self.write("FUNC ")
        self.visit(node.data_type)
        self.write(" ")
        self.visit(node.function_name)
        self.write(" (")
        if len(node.parameter_list)>0:
            for i in node.parameter_list[:-1]:
                if i is None:
                    self.write("<PAR>")
                else:
                    self.visit(i)
                self.write(", ")
            if node.parameter_list[-1] is None:
                self.write("<PAR>")
            else:
                self.visit(node.parameter_list[-1])
        self.write(")")
        self.write()
        
        self.indent += 1
        
        for i in node.data_definitions:
            self.visit(i)
            
        for i in node.statement_list:
            self.visit(i)
            
        if not(node.routine_error is None):
            self.visit(node.routine_error)
        
        if not(node.routine_undo is None):
            self.visit(node.routine_undo)
            
        self.indent -= 1
        self.writeindent()
        self.write("ENDFUNC") 
        
    def visit_TrapDeclarationAST(self, node):
        #procedure_name*, data_definitions**, statement_list**, routine_error*, routine_undo* 
        self.write("TRAP ")
        self.visit(node.procedure_name)
        self.write()
        
        self.indent += 1
        
        for i in node.data_definitions:
            self.visit(i)
            
        for i in node.statement_list:
            self.visit(i)
            
        if not(node.routine_error is None):
            self.visit(node.routine_error)
        
        if not(node.routine_undo is None):
            self.visit(node.routine_undo)
            
        self.indent -= 1
        self.writeindent()
        self.write("ENDTRAP") 
        
    def visit_AssignmentStatementAST(self, node):
        #dest*, source*
        self.writeindent()
        self.visit(node.dest)
        self.write(" := ")
        self.visit(node.source)
        self.write(";")
        self.write()
        
    def visit_GotoStatementAST(self, node):
        #dest*
        self.writeindent()
        self.write("GOTO ")
        self.visit(node.dest)
        self.write(";")
        self.write()
        
    def visit_ReturnStatementAST(self, node):
        #result*
        self.writeindent()
        self.write("RETURN ")
        if not(node.result is None):
            self.visit(node.result)
        self.write(";")
        self.write()
        
    def visit_RaiseStatementAST(self, node):
        #error_number*
        self.writeindent()
        self.write("RAISE ")
        self.visit(node.dest)
        self.write(";")
        self.write()
        
    def visit_ExitStatementAST(self, node):
        self.writeindent()
        self.write("EXIT ;")
        self.write()
    
    def visit_RetryStatementAST(self, node):
        self.writeindent()
        self.write("RETRY ;")
        self.write()
        
    def visit_TrynextStatementAST(self, node):
        self.writeindent()
        self.write("TRYNEXT ;")
        self.write()
        
    def visit_ConnectStatementAST(self, node):
        #connect_taget*, trap*
        self.writeindent()
        self.write("CONNECT ")
        self.visit(node.connect_taget)
        self.write(" WITH ")
        self.visit(node.trap)
        self.write(";")
        self.write()
        
    def visit_IfStatement(self, node):
        #condition*, statement_list**, elseif_list**, else_statement_list**
        self.writeindent()
        self.write("IF ")
        self.visit(node.conditional_expression)
        self.write(" THEN")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        if len(else_statement)>0:
            for i in node.elseif_statement_list:
                self.visit(i)
        if len(else_statement)>0:
            self.writeindent()
            self.write("ELSE")
            self.indent += 1
            for i in node.else_statement:
                self.visit(i)
            self.indent += 1
        self.writeindent()
        self.write("ENDIF")
        self.write()
        
    def visit_ElseIfStatement(self, node):
        #condition*, statement_list**
        self.writeindent()
        self.write("ELSEIF ")
        self.visit(node.condition)
        self.write(" THEN")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        
    def visit_ForStatement(self, node):
        #loop_variable*, ifrom*, ito*, istep*, statement_list**
        self.writeindent()
        self.write("FOR ")
        self.visit(node.loop_variable)
        self.write(" FROM ")
        self.visit(node.ifrom)
        self.write(" TO ")
        self.visit(node.ito)
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
        
    def visit_WhileStatement(self, node):
        #condition*, statement_list**
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
    
    def visit_TestStatement(self, node):
        #expression*, cases**, default**
        self.writeindent()
        self.write("TEST ")
        self.visit(node.expression)
        self.write()
        for i in node.casestatement_list:
            self.visit(i)
        if len(node.defaultstatement)>0:
            self.writeindent()
            self.write("DEFAULT:")
            self.write()
            self.indent += 1
            for i in node.defaultstatement:
                self.visit(i)
            self.indent -= 1
        self.writeindent()
        self.write("ENDTEST")
        self.write()     
        
    def visit_CaseStatement(self, node):
        #test_value*, statement_list**
        self.writeindent()
        if node.test_value is None:
            self.write("<CSE>")
            self.write()
        else:
            self.write("CASE ")
            self.visit(node.test_value)
            self.write(" : ")
            self.write()
            self.indent += 1
            for i in node.statement_list:
                self.visit(i)
            self.indent -= 1   
        

class EvaluateRapidExpression( rapid_ast.NodeVisitor ):
    def __init__(self, modulename, functionname=None):
        self.return_value = None
        self.modulename = modulename
        self.functionname = functionname
        
    def visit_ConstExpressionAST(self, node):
        parse = EvaluateRapidExpression(self.modulename, self.functionname)
        parse.visit( node.expression )
        self.return_value = parse.GetReturn()
        
    def visit_AggregateAST(self, node):
        self.return_value = []
        for i in node.expr:
            parse = EvaluateRapidExpression(self.modulename, self.functionname)
            parse.visit( i )
            self.return_value.append(parse.GetReturn())
            
    def visit_VariableAST(self, node):
        varindexlist = node.index
        varcomponent = node.component
        if varcomponent is None:
            if len(varindexlist)==0:
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse = EvaluateRapidExpression(self.modulename, self.functionname)
                    parse.visit( node.var )
                    getvar = parse.GetReturn()
                else:
                    varname = node.var.name
                    getvar = pyrapid.Symbols().GetSymbol(varname, self.modulename, self.functionname)
                if getvar.type != pyrapid.Symbol.SYM_TYPE_CONST_VAR:
                    raise Exception("Symbol %s has to be a constant variable %d"%(vartype, getvar.type))
                self.return_value = getvar.data.Get()
            else:
                index = []
                for i in varindexlist:
                    parse = EvaluateRapidExpression(self.modulename, self.functionname)
                    parse.visit( i )
                    index.append(parse.GetReturn())
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse = EvaluateRapidExpression(self.modulename, self.functionname)
                    parse.visit( node.var )
                    getvar = parse.GetReturn()
                else:
                    varname = node.var.name
                    getvar = pyrapid.Symbols().GetSymbol(varname, self.modulename, self.functionname)
                if getvar.type != pyrapid.Symbol.SYM_TYPE_CONST_VAR:
                    raise Exception("Symbol %s has to be a constant variable %d"%(vartype, getvar.type))
                self.return_value = getvar.data.GetElem(index).Get()
        else:
            self.visit(node.var)
            varcomponent = varcomponent.name
            self.return_value = self.return_value.GetElem(varcomponent).Get()
            #raise Exception("EvaluateRapidExpression with variable with component not yet supported")
        
    def visit_LiteralATS(self, node):
        self.return_value = node.value
        
    def visit_Operator1AST(self, node):
        parse = EvaluateRapidExpression(self.modulename, self.functionname)
        parse.visit( node.par1 )
        if node.operator == "NOT":
            self.return_value = not parse.GetReturn()
        elif node.operator == "-":
            self.return_value = - parse.GetReturn()
        else:
            raise Exception("operator not supported '%s'"%(node.operator))
            
    def visit_Operator2AST(self, node):
        parse1 = EvaluateRapidExpression(self.modulename, self.functionname)
        parse1.visit( node.par1 )
        parse2 = EvaluateRapidExpression(self.modulename, self.functionname)
        parse2.visit( node.par2 )
        if node.operator == "+":
            self.return_value = parse1.GetReturn() + parse2.GetReturn()
        elif node.operator == "-":
            self.return_value = parse1.GetReturn() - parse2.GetReturn()
        elif node.operator == "*":
            self.return_value = parse1.GetReturn() * parse2.GetReturn()
        elif node.operator == "/":
            self.return_value = float(parse1.GetReturn()) / float(parse2.GetReturn())
        elif node.operator == "DIV":
            self.return_value = parse1.GetReturn() // parse2.GetReturn()
        elif node.operator == "MOD":
            self.return_value = parse1.GetReturn() % parse2.GetReturn()
        elif node.operator == "OR":
            self.return_value = parse1.GetReturn() or parse2.GetReturn()
        elif node.operator == "XOR":
            self.return_value = bool(parse1.GetReturn()) != bool(parse2.GetReturn())
        elif node.operator == "AND":
            self.return_value = parse1.GetReturn() and parse2.GetReturn()
        elif node.operator == "<":
            self.return_value = parse1.GetReturn() < parse2.GetReturn()
        elif node.operator == ">":
            self.return_value = parse1.GetReturn() > parse2.GetReturn()    
        elif node.operator == "<=":
            self.return_value = parse1.GetReturn() <= parse2.GetReturn()
        elif node.operator == ">=":
            self.return_value = parse1.GetReturn() >= parse2.GetReturn()    
        elif node.operator == "=":
            self.return_value = parse1.GetReturn() == parse2.GetReturn()
        elif node.operator == "<>":
            self.return_value = parse1.GetReturn() != parse2.GetReturn()    
        else:
            raise Exception("operator not supported '%s'"%(node.operator))

        
    def visit_ExpressionAST(self, node):
        if node.expr is None:
            raise Expression("node can not be a ConstantExpression")
        elif isinstance(node.expr, rapid_ast.FunctionCallAST):
            raise Expression("node can not be a ConstantExpression, todo for functionCall that works only on contant parameter and use only constand data")
        elif isinstance(node.expr, rapid_ast.VariableAST):
            pass
        elif isinstance(node.expr, rapid_ast.AggregateAST):
            pass
        elif isinstance(node.expr, rapid_ast.Operator1AST):
            pass
        elif isinstance(node.expr, rapid_ast.Operator2AST):
            pass
        elif isinstance(node.expr, rapid_ast.ExpressionAST):
            pass
        elif isinstance(node.expr, rapid_ast.LiteralATS):
            pass
        else:
            raise Exception("programming error")
            
        parse = EvaluateRapidExpression(self.modulename, self.functionname)
        parse.visit( node.expr )
        self.return_value = parse.GetReturn()

        
    def GetReturn(self):
        return self.return_value


class CompareRapid( rapid_ast.NodeCompare ):   
    pass


if __name__ == '__main__':
    import rapid_parser
    text = """
    """
    parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)
    allmodule = parser.parse(text, 'x.rapid', debuglevel=0)
    
    
    
    
    