from browse_rapid_ast import EvaluateRapidExpression, ensure_dir
import rapid_ast
import os
import os.path
import run.pyrapid as pyrapid
import copy
import rapid_parser

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
        self.writemodule("import copy")
        
    def close(self, etrypoint=None):
        if not(entrypoint is None):
            self.writemodule("if __name__ == '__main__':" )
            self.pushModuleScope()
            self.writemodule("pyrapid.Symbols().GetSymbol(%s).data({})"%(repr(entrypoint),))
            self.popModuleScope()
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
        const_python_start = "python:"
        if node.comment.startswith(const_python_start):
            self.writemodule( "# from python comment ...")
            self.writemodule( node.comment[len(const_python_start):])
        else:
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
            
        for i in list_switch:
            old0, old1, old2, old3, old4 = self.params[i]
            old4 = copy.copy(list_switch)
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
        bsym = True
        try:
            bget = self.bGetVariableAST
        except:
            pass
        try:
            bsym = self.bSymVariableAST
        except:
            pass
        if bget:
            bsym = True
        self.bGetVariableAST = False
        #self.bSymVariableAST = True
        if varcomponent is None:
            if len(varindexlist)==0:
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse.visit( node.var )
                else:
                    self.simple_writemodule( "pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s)" % ( repr(node.var.name), repr(self.module_name), repr(self.function_name) ) )
                if bsym:
                    self.simple_writemodule( ".data" )
            else:
                if isinstance(node.var, rapid_ast.VariableAST):
                    parse.visit( node.var )
                else:
                    self.simple_writemodule( "pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data" % ( repr(node.var.name), repr(self.module_name), repr(self.function_name) ) )
                
                self.simple_writemodule( ".GetElem( "  )
                
                for i in varindexlist[:-1]:
                    old = self.bSymVariableAST
                    self.bSymVariableAST = False
                    self.visit( i )
                    self.bSymVariableAST = old
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
        try:
            del self.bSymVariableAST
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
    
    def visit_ProcedureArgumentAST(self, node):    
        #type "Required" or "Optional" or "Conditional" or None
        #argumentname is IdentifierAST or None
        #argumentvalue is ExpressionAST ... or VariableAST or None
        
        if node.type is None:
            raise Exception("error 1")
        
        if node.argumentname is None:
            if isinstance(self.parameters_index, int):
                argumentname = self.parameters_defined.keys()[self.parameters_index]
                self.parameters_index += 1
            else:
                raise Exception("error 2")
        else:
            argumentname = node.argumentname.name
            self.parameters_index = None
        
        self.simple_writeindent()
        self.simple_writemodule( "parameters_actual[%s] = " % (repr(argumentname),))
        if isinstance(node.argumentvalue, rapid_ast.VariableAST):
            if self.parameters_defined[argumentname][1]=="NORMAL":
                vartype = self.parameters_defined[argumentname][2]
                #todo make type compare
                self.bSymVariableAST = False
                self.bGetVariableAST = False
                self.simple_writemodule("copy.deepcopy(")
                self.visit( node.argumentvalue )
                self.simple_writemodule(")")
            elif (self.parameters_defined[argumentname][1]=="VAR") or (self.parameters_defined[argumentname][1]=="PERS") or (self.parameters_defined[argumentname][1]=="INOUT"):
                self.bSymVariableAST = False
                self.bGetVariableAST = False
                self.visit(node.argumentvalue)
            else:
                raise Exception("error 3")
        else:
            if (self.parameters_defined[argumentname][1]=="NORMAL") or (self.parameters_defined[argumentname][1]=="INOUT"):
                vartype = self.parameters_defined[argumentname][2]
                varinstance_size = self.parameters_defined[argumentname][3]
                if varinstance_size==0:
                    self.simple_writemodule("pyrapid.Symbol.CreateVar(pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data(" % ( repr(vartype), repr(self.module_name), repr(self.function_name) ))
                    self.visit( node.argumentvalue )
                    self.simple_writemodule("))")
                else:
                    self.simple_writemodule("pyrapid.Symbol.CreateVar( pyrapid.rapid_array([], pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data, " % ( repr(vartype), repr(self.module_name), repr(self.function_name) ) )
                    self.visit( node.argumentvalue )
                    self.simple_writemodule("))")
            else:
                raise Exception("error 3")
            
        self.simple_writemodule( )
        
        
    def visit_ProcedureCallAST(self, node):
        #procedure is IdentifierAST or ExpressionAST
        #arguments list of ProcedureArgumentAST
        procedure_name = node.procedure.name
        self.writemodule("# Call procedure %s"%(procedure_name,))
        refsym = pyrapid.Symbols().GetSymbol(symbolname=procedure_name, modulename=self.module_name, functionname=self.function_name)
        if refsym is None:
            raise Exception("procedure %s used in module %s function %s not defined"%(procedure_name, self.module_name, self.function_name))
        procedure_call = refsym.data
        if refsym.type != pyrapid.Symbol.SYM_TYPE_PROCEDURE:
            raise Exception("symbol %s used in module %s function %s has to be a procedure"%(procedure_name, self.module_name, self.function_name))
        self.writemodule( "procedure_call = pyrapid.Symbols().GetSymbol(symbolname=%s, modulename=%s, functionname=%s).data" % ( repr(procedure_name), repr(self.module_name), repr(self.function_name) ) )
        self.parameters_defined = refsym.parameters
        #compute parameter list
        self.writemodule("parameters_actual = {}")
        self.parameters_index = 0
        
        for i in node.arguments:
            self.visit(i)
        
        self.writemodule("procedure_call(parameters_actual)")
        self.writemodule("del parameters_actual")
        self.writemodule("del procedure_call")
        self.writemodule("# End Call procedure")
        
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


if __name__ == '__main__':
    import sys
    entrypoint = None
    if len(sys.argv)>1:
        entrypoint = sys.argv[1]
    if len(sys.argv)>2:
        ltext = []
        for i in sys.argv[2:]:
            with open(i,"r") as f:
                ltext.append(f.read())
        text = "\n".join(ltext)
    else:
        text = sys.stdin.read()
    
    parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False, start_from='module_declaration_list')
    allmodule = parser.parse(text, 'x.rapid', debuglevel=0)
    
    traslate = TraslateRapidToPython()
    
    traslate.visit(allmodule)
    traslate.close(entrypoint)
    

