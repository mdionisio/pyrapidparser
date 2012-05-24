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
        return ( node1.name == node2.name)
        
    def compare_ModuleAST(self, node1, node2):
        return True