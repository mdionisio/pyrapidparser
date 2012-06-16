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


class TraslateRapidToPython( rapid_ast.NodeVisitor ):
    
    def __init__(self):
        self.file_init_name = None
        self.file_module_name = None
        self.file_init = None
        self.file_module = None
        self.module_name = None
        self.module_attribute = []
        self.function_name = None
        self.indent_module = 0
        self.indent_init = 0
        self.directory = "run"
        ensure_dir(self.directory)
        self.file_init_name = os.path.join(self.directory, "_rapid_program_init_.py")
        self.file_module_name = os.path.join(self.directory, "rapid_program.py")
        self.file_init = open(self.file_init_name, "w")
        self.file_module = open(self.file_module_name, "w")
        self.writemodule( "#this file is an automatic traslation of rapid code")
        self.writemodule("import pyrapid")
        self.writemodule("from collections import OrderedDict")
        
    def close(self):
        self.file_init.close()
        self.file_module.close()
        
    def simple_writeindent(self):
        if not (self.file_module is None):
            self.file_module.write (" " * self.indent_module)
        
    def simple_writemodule(self, a="\n"):
        if not (self.file_module is None):
            self.file_module.write (a)
                
    def writemodule(self, a):
        if not (self.file_module is None):
            self.file_module.write ((" " * self.indent_module) + a + "\n")
            
    def writeinit(self, a):
        if not (self.file_init is None):
            self.file_init.write ((" " * self.indent_init) + a + "\n")
            
    def pushModuleScope(self):
        self.indent_module += 4
        
    def pushInitScope(self):
        self.indent_init += 4
        
    def popModuleScope(self):
        self.indent_module -= 4
        
    def popInitScope(self):
        self.indent_init -= 4
    
    def visit_IdentifierAST(self, node):
        pass
        
    def visit_ModuleAttributeAST(self, node):
        #ModuleAttributeAST: [ name ]
        self.module_attribute.append(node.name)
        
    def pre_visit_ModuleAST(self, node):
        """
            1. create a folder with module name
            2. create a file __init.__py inside the 1. folder
            3. create a file modulename.py  inside the 1. folder
        """
        self.indent_module = 0
        self.indent_init = 0
        self.function_name = None
        self.module_attribute = []
        
        #module_name*, module_attribute**, type_definitions**, data_definitions**, routine_definitions**
        self.module_name = node.module_name.name
        if self.module_name is None:
            print("Module name not defined default will be used")
            self.module_name = "default"
        
        self.writemodule( "################### Start module %s ####################" % (self.module_name,))
        pyrapid.Symbols().PushScope(modulename=self.module_name, functionname=self.function_name, invalue={})
        self.writemodule( "pyrapid.Symbols().PushScope(%s, %s)"%(repr(self.module_name), repr(self.function_name), ))
        self.writemodule( "##################################################################")
        
        
    def post_visit_ModuleAST(self, node):
        """ 
              1. write on the __init__.py the global symbol
              2. close the opend file
        """
        
        self.writemodule( "##################################################################")
        pyrapid.Symbols().PopScope()
        self.writemodule( "pyrapid.Symbols().PopScope()")
        self.writemodule( "################### End module %s ####################" % (self.module_name,))
        
        self.indent_module = 0
        self.indent_init = 0
        
        self.module_name = None
        self.module_attribute = []
        self.function_name = None
        
        
    def visit_CommentAST(self, node):
        self.writemodule( "# ## COMMENT:" + node.comment +" ##")
        
    def pre_visit_TypeDefAST(self, node):
        self.writemodule("############################# start type definition")
        self.tmp_TypeDefAST_data = node.type
        
    def post_visit_TypeDefAST(self, node):
        del self.tmp_TypeDefAST_data
        self.writemodule("# end type definition")
        
    def visit_AliasDefATS(self, node):
        typename = node.type_name.name
        aliasname = node.alias_name.name
        if typename is None:
            raise Exception("conversion not possible because type_name is not defined")
        if aliasname is None:
            raise Exception("conversion not possible because type_name is not defined")
        
        refsym = pyrapid.Symbols().GetSymbol(typename, self.module_name, self.function_name)
        if refsym is None:
            raise Exception("reference to unknown type")
        if refsym.type != pyrapid.Symbol.SYM_TYPE_DATATYPE:
            raise Exception("ALIAS to symbol that is not a typedef")
        newsym = refsym.data
        
        if self.tmp_TypeDefAST_data is None:
            pyrapid.Symbols().AddGlobalSym(aliasname, pyrapid.Symbol.CreateDataType(newsym))
            self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, pyrapid.Symbol.CreateDataType(pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data))"%(repr(aliasname), repr(typename), repr(self.module_name), repr(self.function_name), ))
        else:
            pyrapid.Symbols().AddModuleSym(self.module_name, aliasname, pyrapid.Symbol.CreateDataType(newsym))
            self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, pyrapid.Symbol.CreateDataType(pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data))"%(repr(self.module_name), repr(aliasname), repr(typename), repr(self.module_name), repr(self.function_name), ))

    def visit_RecordDefAST(self, node):
        record_name = node.record_name.name
        components = node.components

        attributetype= []
        attributename= []
        
        for i in components:
            data_type = i.data_type.name
            record_component_name = i.record_component_name.name
            attributename.append(repr(record_component_name))
            attributetype.append("pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s,functionname=%s).data"%(repr(data_type),repr(self.module_name), repr(self.function_name)))
            
        attributetype = ",".join(attributetype)
        attributename = ",".join(attributename)
            
        record = """
class rapid_%s (pyrapid.rapid_struct):
    def __init__(self, val=None):
        pyrapid.rapid_struct.__init__(self, [ %s ], [ %s ])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, type(self)):
            self.val = val.val
        else:
            pyrapid.rapid_struct.Set(self, val)
""" % (record_name, attributename, attributetype)

        define_class = compile(record,"in_memory_compile","single")
        eval(define_class)

        self.writemodule(record)

        if self.tmp_TypeDefAST_data is None:
            pyrapid.Symbols().AddGlobalSym(record_name, pyrapid.Symbol.CreateDataType(eval("rapid_%s" % (record_name,))))
            self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, pyrapid.Symbol.CreateDataType(rapid_%s))"%(repr(record_name), record_name,))
        else:
            pyrapid.Symbols().AddModuleSym(self.module_name, record_name, pyrapid.Symbol.CreateDataType(eval("rapid_%s" % (record_name,))))
            self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, pyrapid.Symbol.CreateDataType(rapid_%s))"%(repr(self.module_name), repr(record_name), record_name, ))
            
        self.writemodule("del rapid_%s"%(record_name,))

    def pre_visit_DataDefATS(self, node):
        self.writemodule("############################# start declaration")
        self.tmp_DataDefATS_data = node.type
        
    def post_visit_DataDefATS(self, node):
        del self.tmp_DataDefATS_data
        self.writemodule("# end declaration")
        
        
    def VarConstPersDeclaration(self, node, createvar, createvars):
        scope = self.tmp_DataDefATS_data
        vartype = node.type.name
        varinstance_name = node.variable_instance.name.name
        varinstance_value = node.variable_instance.value
        varinstance_size = node.variable_instance.size
            
        if not(varinstance_value is None):
            compute = EvaluateRapidExpression(self.module_name, self.function_name)
            compute.visit(varinstance_value)
            varinstance_value = compute.return_value
                
        if len(varinstance_size)==0:
            getvar = createvar(pyrapid.Symbols().GetSymbol(vartype, self.module_name, self.function_name).data(varinstance_value))
            sgetvar = "%s(pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data(%s))" % ( createvars, repr(vartype), repr(self.module_name), repr(self.function_name), repr(varinstance_value) )
        else:
            size = []
            for i in varinstance_size:
                compute = EvaluateRapidExpression(self.module_name, self.function_name)
                compute.visit(i)
                size.append(compute.return_value)
            getvar = createvar(   pyrapid.rapid_array(size, pyrapid.Symbols().GetSymbol(vartype, self.module_name, self.function_name).data, varinstance_value ) )
            sgetvar = "%s( pyrapid.rapid_array(%s, pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data, %s) )" % ( createvars, str(size), repr(vartype), repr(self.module_name), repr(self.function_name), repr(varinstance_value) )
            
        return (varinstance_name, getvar, sgetvar)
            
        
    def visit_VarDeclarationAST(self, node):
        varinstance_name, getvar, sgetvar = self.VarConstPersDeclaration(node, pyrapid.Symbol.CreateVar, "pyrapid.Symbol.CreateVar")
        
        if self.tmp_DataDefATS_data is None:
            if self.function_name is None:
                #module declaration it is GLOBAL
                pyrapid.Symbols().AddGlobalSym( varinstance_name, getvar ) 
                self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                print "warning: variable %s is local to the function %s"%(varinstance_name, self.function_name)
                pyrapid.Symbols().AddScopeSym( varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddScopeSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
        else:
            if self.function_name is None:
                #module declaration it is LOCAL in the module
                pyrapid.Symbols().AddModuleSym( self.module_name, varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, %s)"%(repr(self.module_name), repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                pyrapid.Symbols().AddScopeSym( varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddScopeSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
        
    def visit_ConstDeclarationAST(self, node):
        varinstance_name, getvar, sgetvar = self.VarConstPersDeclaration(node, pyrapid.Symbol.CreateConst, "pyrapid.Symbol.CreateConst")
        
        if self.tmp_DataDefATS_data is None:
            if self.function_name is None:
                #module declaration it is GLOBAL
                pyrapid.Symbols().AddGlobalSym( varinstance_name, getvar ) 
                self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                print "warning: variable %s is local to the function %s"%(varinstance_name, self.function_name)
                pyrapid.Symbols().AddScopeSym( varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddScopeSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
        else:
            if self.function_name is None:
                #module declaration it is LOCAL in the module
                pyrapid.Symbols().AddModuleSym( self.module_name, varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, %s)"%(repr(self.module_name), repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                pyrapid.Symbols().AddScopeSym( varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddScopeSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
    
    def visit_PersDeclarationAST(self, node):
        varinstance_name, getvar, sgetvar = self.VarConstPersDeclaration(node, pyrapid.Symbol.CreatePers, "pyrapid.Symbol.CreatePers")
        
        if self.tmp_DataDefATS_data is None:
            if self.function_name is None:
                #module declaration it is GLOBAL
                pyrapid.Symbols().AddGlobalSym( varinstance_name, getvar ) 
                self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                pyrapid.Symbols().AddScopeSym( varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddScopeSym(%s, %s)"%(repr(varinstance_name), sgetvar) )
        else:
            if self.function_name is None:
                #module declaration it is LOCAL in the module
                pyrapid.Symbols().AddModuleSym( self.module_name, varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, %s)"%(repr(self.module_name), repr(varinstance_name), sgetvar) )
            else:
                #function declaration it is in the Scope of the function
                pyrapid.Symbols().AddLocalSym(self.module_name, self.function_name, varinstance_name, getvar )
                self.writemodule( "pyrapid.Symbols().AddLocalSym($s, %s, %s, %s)"%(repr(self.module_name), repr(self.function_name), repr(varinstance_name), sgetvar) )
        
    def pre_visit_RoutineDeclarationATS(self, node):
        self.writemodule("############################# start routine declaration")
        self.tmp_outineDeclarationATS_data = node.type
        
    def post_visit_RoutineDeclarationATS(self, node):
        del self.tmp_outineDeclarationATS_data
        self.writemodule("# end routine declaration")
        
    def visit_ParameterDefinitionAST(self, node):
        #parameter_type stringa
        #type IdentifierAST
        #name IdentifierAST
        #size int or None
        paramtype = node.parameter_type
        pname = node.name.name
        ptype = node.type.name
        psize = node.size
        
        self.lastparamadded = pname
        
        if self.params.has_key(pname):
            raise Exception("parameter %s already defined"%(pname,))
        else:
            self.params[pname] = ("required", paramtype, ptype, psize, [])
    
    def visit_OptionalParameterDefinitionAST(self, node):
        #parameter None or ParameterDefinitionAST or SwitchParameterDefinitionAST
        #switchs list of None or ParameterDefinitionAST or SwitchParameterDefinitionAST

        self.visit(node.parameter)
        if self.params.has_key(pname):
            raise Exception("parameter %s already defined"%(pname,))
        
        list_switch = set()
        list_switch.update([self.lastparamadded])
            
        for i in node.switchs:
            self.visit(i)
            list_switch.update([self.lastparamadded])
            
        from copy import copy
        for i in list_switch:
            old0, old1, old2, old3, old4 = self.params[i]
            old4 = copy(list_switch)
            old4.remove(i)
            self.params[self.lastparamadded] = ( "optional", old1, old2, old3, list(old4) ) 
        
    
    def visit_SwitchParameterDefinitionAST(self, node):
        #name IdentifierAST
        pname = node.name.name
        
        self.lastparamadded = pname
        
        if self.params.has_key(pname):
            raise Exception("parameter %s already defined"%(pname,))
        else:
            self.params[pname] = ("switch", None, None, None, [])
            
    def visit_ExpressionAST(self, node):
        #expr is None or AggregateAST or Operator1AST or Operator2AST or FunctionCallAST or VariableAST or ExpressionAST or LiteralATS
        if node.expr is None:
            return
        else:
            self.visit(node.expr)
            
    def visit_AggregateAST(self, node):
        self.simple_writemodule("[")
        if len(node.expr)>0:
            for i in node.expr[:-1]:
                self.visit(i)
                self.simple_writemodule(", ")
            self.visit(node.expr[-1])
        self.simple_writemodule("]")
        
    def visit_Operator1AST(self, node):
        if not(node.operator is None):
            self.simple_writemodule("( not ")
            self.visit(node.par1)
            self.simple_writemodule(" )")
        else:
            self.visit(node.par1)
        
    def visit_Operator2AST(self, node):
        self.simple_writemodule("( ")
        self.visit(node.par1)
        self.simple_writemodule(" ")
        if node.operator == "=":
            self.simple_writemodule("==")
        else:
            self.simple_writemodule(node.operator)
        self.simple_writemodule(" ")
        self.visit(node.par2)
        self.simple_writemodule(" )")
            
    def visit_LiteralATS(self, node):
        #value is int or float or string
        if isinstance(node.value, str):
            self.simple_writemodule(repr(node.value))
        else:
            self.simple_writemodule(str(node.value))
            
    def visit_VariableAST(self, node):
        varindexlist = node.index
        varcomponent = node.component
        bget = True
        try:
            bget = self.bGetVariableAST
            del self.bGetVariableAST
        except:
            pass
        self.bGetVariableAST = False
        if varcomponent is None:
            if len(varindexlist)==0:
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse.visit( node.var )
                else:
                    self.simple_writemodule( "pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data" % ( repr(node.var.name), repr(self.module_name), repr(self.function_name) ) )
            else:
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse.visit( node.var )
                else:
                    self.simple_writemodule( "pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data" % ( repr(node.var.name), repr(self.module_name), repr(self.function_name) ) )
                
                self.simple_writemodule( ".GetElem( "  )
                
                for i in varindexlist[:-1]:
                    self.visit( i )
                    self.simple_writemodule( ", ")
                self.visit( varindexlist[-1] )
                    
                self.simple_writemodule( " )" )
        else:
            if isinstance(node.var, rapid_ast.VariableAST):
                self.visit(node.var)
                self.simple_writemodule( ".GetElem(%s)" % ( repr(varcomponent.name), ) )
            else:
                raise Exception("if there is a component we need a variable as data before .")

        if bget:
            self.simple_writemodule( ".Get()" )
        try:
            del self.bGetVariableAST
        except:
            pass
            
    def visit_AssignmentStatementAST(self, node):
        #dest* is VariableAST
        #, source*
        self.simple_writeindent()
        self.bGetVariableAST = False
        self.visit(node.dest)
        self.simple_writemodule( ".Set( " )
        self.visit(node.source)
        self.simple_writemodule(" ) ")
        self.simple_writemodule()
        
    def visit_GotoStatementAST(self, node):
        raise Exception("GOTO not yet supported")
        
    def visit_ReturnStatementAST(self, node):
        self.simple_writeindent()
        if node.result is None:
            self.simple_writemodule( "return " )
        else:
            self.simple_writemodule( "return ( " )
            self.visit(node.source)
            self.simple_writemodule(" )")
        self.simple_writemodule()
        
    def visit_ExitStatementAST(self, node):
        self.writemodule("import sys")
        self.writemodule("sys.exit(1)")
        
    def visit_RetryStatementAST(self, node):
        raise Exception("Retry not yet supported")
        
    def visit_TrynextStatementAST(self, node):
        raise Exception("Try next not yet supported")
        
    def visit_ConnectStatementAST(self, node):
        raise Exception("Connect not yet supported")
        
    def visit_IfStatement(self, node):
        #condition*, statement_list**, elseif_list**, else_statement_list**
        self.simple_writeindent()
        self.simple_writemodule( "if (" )
        self.visit(node.condition)
        self.simple_writemodule( ") :" )
        self.simple_writemodule()
        self.pushModuleScope()
        if len(node.statement_list)==0:
            self.writemodule("pass")
        
        for i in node.statement_list:
            self.visit(i)
        
        self.popModuleScope()
        for i in node.elseif_list:
            self.visit(i)
        
        if len(node.else_statement_list)>0:
            self.writemodule("else:")
            self.pushModuleScope()
            for i in node.else_statement_list:
                self.visit(i)
            self.popModuleScope()
        
    def visit_ElseIfStatement(self, node):    
        #condition*, statement_list**
        self.simple_writeindent()
        self.simple_writemodule( "elif (" )
        self.visit(node.condition)
        self.simple_writemodule( ") :" )
        self.simple_writemodule()
        self.pushModuleScope()
        if len(node.statement_list)==0:
            self.writemodule("pass")
        
        for i in node.statement_list:
            self.visit(i)
        
        self.popModuleScope()
        
    def visit_ProcedureDeclarationAST(self, node):
        #procedure_name*, parameter_list**, data_definitions**, statement_list**, routine_backward*, routine_error*, routine_undo*
        self.function_name =  node.procedure_name.name
        from collections import OrderedDict
        self.params = OrderedDict()
        self.lastparamadded = None
        
        self.paramslist = []
        for i in node.parameter_list:
            #ParameterDefinitionAST or OptionalParameterDefinitionAST or SwitchParameterDefinitionAST or None
            self.visit(i)
        
        params = repr(self.params)
            
        proc = "def rapid_proc_%s (local_args_scope):" % (self.function_name)

        def _rapid_proc_(local_args_scope):
            pass

        self.writemodule(proc)
        
        if self.tmp_outineDeclarationATS_data is None:
            pyrapid.Symbols().AddGlobalSym(self.function_name, pyrapid.Symbol.CreateProcedure(self.params, _rapid_proc_))
        else:
            pyrapid.Symbols().AddModuleSym(self.module_name, self.function_name, pyrapid.Symbol.CreateProcedure(self.params, _rapid_proc_))
            
        self.pushModuleScope()
        
        pyrapid.Symbols().PushScope(modulename=self.module_name, functionname=self.function_name, invalue={})
        
        for ik,iv in self.params.iteritems():
            vartype, paramtype, ptype, psize, pdep = iv
            if psize==0:
                getvar = pyrapid.Symbol.CreateVar(pyrapid.Symbols().GetSymbol(ptype, self.module_name, self.function_name).data())
            else:
                getvar = pyrapid.Symbol.CreateVar(pyrapid.rapid_array([], pyrapid.Symbols().GetSymbol(ptype, self.module_name, self.function_name).data) )
            pyrapid.Symbols().AddScopeSym(ik, getvar)
        
        self.writemodule( "pyrapid.Symbols().PushScope(modulename=%s, functionname=%s, invalue=local_args_scope)"%(repr(self.module_name), repr(self.function_name)))
        
        self.writemodule("# data definitions")
        
        for i in node.data_definitions:
            self.visit(i)
        
        self.writemodule("# stantments")
        
        for i in node.statement_list:
            self.visit(i)
        
        self.writemodule("# backward stantment")
        
        if not ( node.routine_backward is None ):
            self.visit(node.routine_backward)
        
        self.writemodule("# error stantment")
        
        if not ( node.routine_error is None ):    
            self.visit(node.routine_error)
        
        self.writemodule("# error undo")
        
        if not ( node.routine_undo is None ):
            self.visit(node.routine_undo)
            
        self.writemodule("# end stantment")
        
        self.writemodule("pyrapid.Symbols().PopScope()")
        self.popModuleScope()
        pyrapid.Symbols().PopScope()
        
        if self.tmp_outineDeclarationATS_data is None:
            self.writemodule( "pyrapid.Symbols().AddGlobalSym(%s, pyrapid.Symbol.CreateProcedure(%s, rapid_proc_%s))"%(repr(self.function_name), params, self.function_name,))
        else:
            self.writemodule( "pyrapid.Symbols().AddModuleSym(%s, %s, pyrapid.Symbol.CreateProcedure(%s, rapid_proc_%s))"%(repr(self.module_name), params, repr(self.function_name), self.function_name, ))
            
        self.writemodule("del rapid_proc_%s" % (self.function_name,))
        
        del self.params
        
    #
        

class CompareRapid( rapid_ast.NodeCompare ):   
    pass


if __name__ == '__main__':
    import rapid_parser
    text = """
MODULE syun1
! pippo
    LOCAL ALIAS num pippo;
    ALIAS num pippo1;
    LOCAL RECORD prova
        num usecount;
    ENDRECORD
    CONST prova p1 := [ 100 ];
    CONST num n1 := p1.usecount;
    CONST num c1:=10;
    CONST num c2:=c1+1;
    VAR num a1:=1;
    CONST num a3{3} := [ 10, 30, 50 ];
    LOCAL VAR num a4:=12;
    VAR num a5 := a3{2};
    VAR string s1:="pippo";
    VAR bool b := TRUE;
    PROC PIPPO(VAR num p1, VAR num p2{*})
        VAR num p10 := 1;
        VAR num p11{3} := [ 10, 30, 50 ];
        VAR prova p12 := [ 100 ];
        VAR prova p13{3};
        
        a5 := 1;
        a5 := 1+2*3;
        a5 := (1+2)*3;
        p11{2} := a5;
        p12.usecount := p11{2};
        p13{1}.usecount :=p12.usecount;
        p13{2}.usecount :=p13{2}.usecount;
        IF b THEN
            a5 := 2;
        ELSEIF B = FALSE THEN
            a6 := 3;
        ELSE
            a5 := 6;
        ENDIF
        
        IF b = TRUE THEN
            a5 := 2;
        ENDIF
    ENDPROC
ENDMODULE
    """
    parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)
    allmodule = parser.parse(text, 'x.rapid', debuglevel=0)
    
    traslate = TraslateRapidToPython()
    
    traslate.visit(allmodule)
    traslate.close()
    
    
    
    