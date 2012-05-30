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
    
    def visit_CommentAST(self, node):        
        self.writeln("!"+node.comment)
        
    def visit_ModuleAST(self, node):
        #module_name*, module_attribute**, type_definitions**, data_definitions**, routine_definitions**
        self.writeindent()
        if node.module_name.name is None:
            self.write("MODULE <ID> ")
        else:
            self.write("MODULE %s "%(node.module_name.name))
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
        self.write(node.type_name.name) 
        self.write(" ") 
        self.write(node.alias_name.name) 
        self.write(";") 
        
    def visit_RecordDefAST(self, node):     
        self.write("RECORD ") 
        self.write(node.record_name.name) 
        self.write() 
        self.indent += 1
        for i in node.components:
            self.visit(i)
        self.indent -= 1
        self.writeindent()
        self.write("ENDRECORD") 
        
    def visit_RecordComponentDefAST(self, node):     
        self.writeln("RECORD %s %s;"%(node.data_type.name,node.record_component_name.name)) 
        
        

class EvaluateRapidExpression( rapid_ast.NodeVisitor ):
    def __init__(self, symbols=None):
        self.return_value = None
        self.symbols = symbols
        
    def visit_ConstExpressionAST(self, node):
        parse = EvaluateRapidExpression()
        parse.visit( node.expression )
        self.return_value = parse.GetReturn()
        
    def visit_AggregateAST(self, node):
        self.return_value = []
        for i in node.expr:
            parse = EvaluateRapidExpression()
            parse.visit( i )
            self.return_value.append(parse.GetReturn())
            
    def visit_LiteralATS(self, node):
        self.return_value = node.value
        
    def visit_Operator1AST(self, node):
        parse = EvaluateRapidExpression()
        parse.visit( node.par1 )
        if node.operator == "NOT":
            self.return_value = not parse.GetReturn()
        else:
            raise Exception("operator not supported '%s'"%(node.operator))
            
    def visit_Operator2AST(self, node):
        parse1 = EvaluateRapidExpression()
        parse1.visit( node.par1 )
        parse2 = EvaluateRapidExpression()
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
            raise Expression("node can not be a ConstantExpression, todo for VariableAST that is constant")
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
            
        parse = EvaluateRapidExpression()
        parse.visit( node.expr )
        self.return_value = parse.GetReturn()

        
    def GetReturn(self):
        return self.return_value


class TraslateRapidToPython( rapid_ast.NodeVisitor ):
    
    def __init__(self):
        self.default_symbol = { "num":("VARTYPE", pyrapid.rapid_num), "string":("VARTYPE", pyrapid.rapid_string) }
        self.global_symbol = copy.copy(self.default_symbol)
        self.scope_symbol = [  { } ]
        self.file_init_name = None
        self.file_module_name = None
        self.file_init = None
        self.file_module = None
        self.module_name = None
        self.module_attribute = []
        self.indent_module = 0
        self.indent_init = 0
        self.directory = "run"
        
    def PushScope(self):
        self.scope_symbol.append({})
        
    def PopScope(self):
        return self.scope_symbol
        
    def GetSymbol(self, symbolname):
        for i in range(len(self.scope_symbol)-1,-1,-1):
            if self.scope_symbol[i].has_key(symbolname):
                return self.scope_symbol[i][symbolname]
        return self.GetGlobalSym(symbolname)
        
    def AddSym(self, symbolname, data):
        if self.scope_symbol[-1].has_key(symbolname):
            raise Exception("symbol %s already defined"%(symbolname,))
        else:
            self.scope_symbol[-1][symbolname] = data
        
    def AddGlobalSym(self, symbolname, data):
        if self.global_symbol.has_key(symbolname):
            raise Exception("symbol %s already defined"%(symbolname,))
        else:
            self.global_symbol[symbolname] = data
            
    def IsGlobalSymDefined(self, symbolname):
        if self.global_symbol.has_key(symbolname):
            return True
        return False
        
    def GetGlobalSym(self, symbolname):
        if self.global_symbol.has_key(symbolname):
            return self.global_symbol[symbolname]
        return None
        
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
        
        #module_name*, module_attribute**, type_definitions**, data_definitions**, routine_definitions**
        self.module_name = node.module_name.name
        if self.module_name is None:
            print "Module name not defined default will be used"
            self.module_name = "default"
        ensure_dir(self.directory)
        self.file_init_name = os.path.join(self.directory, "_module_init_.py")
        self.file_module_name = os.path.join(self.directory, "%s.py" % (self.module_name,))
        self.file_init = open(self.file_init_name, "w")
        self.file_module = open(self.file_module_name, "w")
        
        self.writemodule( """
#this file is an automatic traslation of rapid code
""")

        self.writemodule("from pyrapid import *")
        
    def post_visit_ModuleAST(self, node):
        """ 
              1. write on the __init__.py the global symbol
              2. close the opend file
        """
        allsymbol = ", ".join( [ str(i) for i in self.global_symbol.iterkeys() if not self.default_symbol.has_key(i)] )
        
        self.writeinit( "import pyrapid" )
        self.writeinit( "import %s"%(self.module_name,) )
        self.writeinit( "pyrapid.global_symbol.update(%s.global_symbol)"%(self.module_name) )
        self.writeinit( "from %s import %s"%(self.module_name, allsymbol)  )
        for i in self.global_symbol.iterkeys() :
            if not self.default_symbol.has_key(i):
                self.writemodule("global_symbol[%s]=__name__"%(repr(i),))
        self.writemodule( "module_attribute = %s" % (repr(self.module_attribute),) )
        self.file_init.close()
        self.file_init = None
        self.file_module.close()
        self.file_module = None
        
    def visit_CommentAST(self, node):
        self.writemodule( "# " + node.comment )
        
    def pre_visit_TypeDefAST(self, node):
        self.tmp_TypeDefAST_data = node.type
        
    def post_visit_TypeDefAST(self, node):
        del self.tmp_TypeDefAST_data
        
    def visit_AliasDefATS(self, node):
        typename = node.type_name.name
        aliasname = node.alias_name.name
        if typename is None:
            raise Exception("conversion not possible because type_name is not defined")
        if aliasname is None:
            raise Exception("conversion not possible because type_name is not defined")
        
        refsym = self.GetSymbol(typename)
        if refsym is None:
            raise Exception("reference to unknown type")
        if refsym[0]!="VARTYPE":
            raise Exception("ALIAS to symbol that is not a typedef")
        newsym = refsym
        
        if self.tmp_TypeDefAST_data is None:
            self.AddGlobalSym(aliasname, newsym)
        else:
            self.AddSym(aliasname, newsym )
            #add to the actual scope
            
        self.writemodule("%s = %s" % (aliasname, newsym[1].__name__))
        
    #record
    
    #
        
        

class CompareRapid( rapid_ast.NodeCompare ):   
    pass
    
        


if __name__ == '__main__':
    
    n1 = []                                                                    # module property
    n2 = rapid_ast.IdentifierAST("test_module")         # module name
    n6 = rapid_ast.IdentifierAST("num")                     # type of variable 
    n7 = rapid_ast.IdentifierAST("pippo")                 # alias name
    n5 = rapid_ast.AliasDefATS( n6, n7)                     # definition of alias
    n8 = rapid_ast.IdentifierAST("pippo1")                 # alias name
    n9 = rapid_ast.AliasDefATS( n6, n8)                     # definition of alias
    datatype = [ rapid_ast.CommentAST("pippo"), rapid_ast.TypeDefAST("LOCAL", n5), rapid_ast.TypeDefAST(None, n9) ]         # list of action
    datadeclaration = []
    code = []
    allmodule = rapid_ast.ModuleAST(n2, n1, datatype, datadeclaration, code)
    
    with open("text.rapid","wt") as f:
        rewrite = WriteRapid(f)
        rewrite.visit(allmodule)
    
    traslate = TraslateRapidToPython()
    
    traslate.visit(allmodule)
    
    evalexpr = rapid_ast.LiteralATS(1)
    evalexpression = rapid_ast.ExpressionAST(evalexpr)
    evaldata = rapid_ast.ConstExpressionAST(evalexpression)
    
    constanteval = EvaluateRapidExpression()
    constanteval.visit(evaldata)
    print "data1 %s"%(str(constanteval.GetReturn()),)
    
    evalexpr1 = rapid_ast.LiteralATS(1)
    evalexpr2 = rapid_ast.LiteralATS(2)
    evalaggr = rapid_ast.AggregateAST([evalexpr1, evalexpr2])
    evalexpression = rapid_ast.ExpressionAST(evalaggr)
    evaldata = rapid_ast.ConstExpressionAST(evalexpression)
    
    constanteval = EvaluateRapidExpression()
    constanteval.visit(evaldata)
    print "data2 %s"%(str(constanteval.GetReturn()),)
    
    evalexpr1 = rapid_ast.LiteralATS(True)
    evalaggr = rapid_ast.Operator1AST("NOT", evalexpr1)
    evalexpression = rapid_ast.ExpressionAST(evalaggr)
    evaldata = rapid_ast.ConstExpressionAST(evalexpression)
    
    constanteval = EvaluateRapidExpression()
    constanteval.visit(evaldata)
    print "data3 %s"%(str(constanteval.GetReturn()),)
    
    evalexpr1 = rapid_ast.LiteralATS(1)
    evalexpr2 = rapid_ast.LiteralATS(2)
    evalaggr = rapid_ast.Operator2AST("+", evalexpr1, evalexpr2)
    evalexpression = rapid_ast.ExpressionAST(evalaggr)
    evaldata = rapid_ast.ConstExpressionAST(evalexpression)
    
    constanteval = EvaluateRapidExpression()
    constanteval.visit(evaldata)
    print "data4 %s"%(str(constanteval.GetReturn()),)
    
    
    