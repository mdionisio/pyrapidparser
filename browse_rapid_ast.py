import rapid_ast
import os
import os.path
import pyrapid
import copy

def ensure_dir(f):
    d = os.path.dirname(f)
    if len(d)==0:
        d = f
    if not os.path.exists(d):
        os.makedirs(d)



class TraslateRapidToPython( rapid_ast.NodeVisitor ):
    
    def __init__(self):
        self.default_symbol = { "num":("VARTYPE", pyrapid.num) }
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
        ensure_dir(self.module_name)
        self.file_init_name = os.path.join(self.module_name, "__init__.py")
        self.file_module_name = os.path.join(self.module_name, "%s.py" % (self.module_name,))
        self.file_init = open(self.file_init_name, "w")
        self.file_module = open(self.file_module_name, "w")
        
        self.writemodule( """
#this file is an automatic traslation of rapid code
""")

        self.writemodule("from pyrapid import num")
        
    def post_visit_ModuleAST(self, node):
        """ 
              1. write on the __init__.py the global symbol
              2. close the opend file
        """
        allsymbol = ", ".join( [ str(i) for i in self.global_symbol.iterkeys() if not self.default_symbol.has_key(i)] )
        
        self.writeinit( "from test_module import " + allsymbol  )
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
            
        self.writemodule("%s = %s" % (aliasname, typename))
        
        

class CompareRapid( rapid_ast.NodeCompare ):
    
    def compare_IdentifierAST(self, node1, node2):
        return ( node1.name == node2.name  )
        
    def compare_ModuleAttributeAST(self, node1, node2):
        return ( node1.name == node2.name )
        
    def compare_ModuleAST(self, node1, node2):
        return True
    
    def compare_CommentAST(self, node1, node2):
        return ( node1.comment == node2.comment )        
        
    def compare_TypeDefAST(self, node1, node2):
        return ( node1.type == node2.type )        
    
    def compare_AliasDefATS(self, node1, node2):
        return True
    
    def compare_RecordDefAST(self, node1, node2):
        return True
        
    def compare_RecordComponentDefAST(self, node1, node2):
        return True    
    
        


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
    
    traslate = TraslateRapidToPython()
    
    traslate.visit(allmodule)