import rapid_ast


class TraslateRapidToPython( rapid_ast.NodeVisitor ):
    
    def visit_IdentifierAST(self, node):
        print "IdentifierAST"
        
    def visit_ModuleAttributeAST(self, node):
        print "ModuleAttributeAST"
        
    def visit_ModuleAST(self, node):
        print "ModuleAST"
        

class CompareRapid( rapid_ast.NodeCompare ):
    
    def compare_IdentifierAST(self, node1, node2):
        return ( node1.name == node2.name  )
        
    def compare_ModuleAttributeAST(self, node1, node2):
        return ( node1.name == node2.name )
        
    def compare_ModuleAST(self, node1, node2):
        return True
    
    def compare_CommentAST(self, node1, node2):
        return ( node1.comment == node2.comment )        


if __name__ == '__main__':
    n1 = rapid_ast.ModuleAttributeAST([])
    n2 = rapid_ast.IdentifierAST("syun1")
    n3 = rapid_ast.ModuleAST(n2, [n1], [], [], [])
    
    a1 = rapid_ast.ModuleAttributeAST([])
    a2 = rapid_ast.IdentifierAST("bobobo")
    a3 = rapid_ast.ModuleAST(a2, [a1], [], [], [])
    
    compare = CompareRapid()
    
    #print compare.full_compare(a3, n3)
    
    n1 = []
    n2 = rapid_ast.IdentifierAST("syun1")
    n6 = rapid_ast.IdentifierAST("num")
    n7 = rapid_ast.IdentifierAST("pippo")
    n5 = rapid_ast.AliasDefATS( n6, n7)
    n4 = [ rapid_ast.TypeDefAST("LOCAL", n5) ]
    n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
    
    print compare.full_compare(n5, n5)