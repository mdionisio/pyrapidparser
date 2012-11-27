#!/usr/bin/python
from browse_rapid_ast import ensure_dir
import rapid_ast
import rapid_parser
import os
import os.path

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
        
    def visit_ProcedureCallAST(self, node, **kwargs):
        #procedure is IdentifierAST or ExpressionAST
        #arguments list of ProcedureArgumentAST
        self.writeindent()
        self.visit(node.procedure)
        if len(node.arguments)>0:
            for i in node.arguments[:-1]:
                self.visit(i)
            self.visit(node.arguments[-1])
        self.write(";")
        self.write()
        
    def visit_VariableAST(self, node):
        if (node.var is None) and (len(node.index)==0) and (node.component is None):
            self.write("<VAR>")
        elif  (len(node.index)==0) and (node.component is None):
            self.visit(node.var)
        elif  (node.component is None):
            self.visit(node.var)
            self.write("{")
            for i in node.index:
                self.visit(i)
                #self.write(i)
                self.write(", ")
            self.visit(node.index[-1])
            #self.write(node.index[-1])
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
        if isinstance(node.value, str):
            self.write('"%s"'%(node.value,))
        else:
            self.write("%s"%(str(node.value),))
        
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
            if node.parameter_type!="NORMAL":
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
        self.visit(node.condition)
        self.write(" THEN")
        self.write()
        self.indent += 1
        for i in node.statement_list:
            self.visit(i)
        self.indent -= 1
        if len(node.elseif_list)>0:
            for i in node.elseif_list:
                self.visit(i)
        if len(node.else_statement_list)>0:
            self.writeindent()
            self.write("ELSE")
            self.indent += 1
            for i in node.else_statement_list:
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
     

if __name__ == '__main__':
    import sys
    
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", action="store", type="string", dest="filename", default="rapid_program.mod",
                        help="output filename", metavar="FILE")
    parser.add_option("-d", "--directory", action="store", type="string", dest="directory", default="test",
                        help="output directory", metavar="DIRECTORY")
                        
    parser.add_option("-i", "--infile", action="store", type="string", dest="infiles",
                        help="input file to convert", metavar="FILE")
                        
    
    (options, args) = parser.parse_args()
        
    text = ""
    filename = ""
    if not (options.infiles is None):
        filename = options.infiles
        with open(filename,"rU") as f:
            text = f.read()
    
    parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False, start_from='module_declaration_list')
    attriblist = parser.parse(text, filename, debuglevel=0).module_list
    
    allmodule = rapid_ast.ModulesAST(attriblist)
    
    filename = os.path.join(options.directory, options.filename)
    with open(filename,"w+t") as f:   
        traslate = WriteRapid(filew=f)
        traslate.visit(allmodule)
        
    

