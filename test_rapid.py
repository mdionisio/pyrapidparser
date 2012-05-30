import unittest
import rapid_ast
import browse_rapid_ast


# functions
def whoami():
    import inspect
    return inspect.stack()[1][3]


class TestBaseFunctions(unittest.TestCase):
    
    def setUp(self):
        pass
        
    @classmethod
    def setUpClass(cls):
        pass
    
    def test_import_rapid_lexer(self):
        try:
            import rapid_lexer
        except:
            rapid_lexer = None
        self.assertIsNotNone(rapid_lexer, "error importing rapid_lexer")
    
    def test_import_rapid_parser(self):
        try:
            import rapid_parser
        except:
            rapid_parser = None
        self.assertIsNotNone(rapid_parser, "error importing rapid_parser")
        
    def test_create_parser(self):
        import rapid_parser
        try:
            parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)
        except:
            parser = None
            
           
        self.assertIsNotNone(parser, "error creating parser")
        
            
    def tearDown(self) :
        pass
        
class TestParserFunctions(unittest.TestCase):
        
    @classmethod
    def setUpClass(cls):
        import rapid_parser
        cls.parser = rapid_parser.RAPIDParser(lex_optimize=True, yacc_debug=False, yacc_optimize=False)
        
    def test_rapid_empty(self):
        text = r"""
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)           
        self.assertIsNone(res, "there is nothing")
    
    def test_rapid_module_1(self):
        text = r"""
MODULE syun1
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing module")
    
    
    def test_rapid_module_2(self):
        text = r"""
MODULE syun1(SYSMODULE)
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = [ rapid_ast.ModuleAttributeAST("SYSMODULE") ]
        n2 = rapid_ast.IdentifierAST("syun1")
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing module")
        
    def test_rapid_module_3(self):
        text = r"""
MODULE <ID>
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = [ ]
        n2 = rapid_ast.IdentifierAST(None)
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing module")
        
    def test_rapid_type_definitions_comment_1(self):
        text = r"""
MODULE syun1
    !pippo
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = [ ]
        n2 = rapid_ast.IdentifierAST("syun1")
        n4 = [ rapid_ast.CommentAST("pippo") ]
        n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing comment in type definition")
        
    def test_rapid_type_definitions_1(self):
        text = r"""
MODULE syun1
    <TDN>
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n4 = [ rapid_ast.TypeDefAST(None, None) ]
        n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing <TDN>")
        
    def test_rapid_type_definitions_alias_1(self):
        text = r"""
MODULE syun1
    ALIAS num pippo;
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("num")
        n7 = rapid_ast.IdentifierAST("pippo")
        n5 = rapid_ast.AliasDefATS( n6, n7)
        n4 = [ rapid_ast.TypeDefAST(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing ALIAS")
        
    def test_rapid_type_definitions_alias_2(self):
        text = r"""
MODULE syun1
    LOCAL ALIAS num pippo;
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("num")
        n7 = rapid_ast.IdentifierAST("pippo")
        n5 = rapid_ast.AliasDefATS( n6, n7)
        n4 = [ rapid_ast.TypeDefAST("LOCAL", n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing ALIAS")
        
    def test_rapid_type_definitions_record_1(self):
        text = r"""
MODULE syun1
    LOCAL RECORD prova
        num usecount;
    ENDRECORD
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("prova")
        n7 = rapid_ast.IdentifierAST("num")
        n8 = rapid_ast.IdentifierAST("num")
        n9 = [ rapid_ast.RecordComponentDefAST(n7, n8) ]
        n5 = rapid_ast.RecordDefAST( n6, n9)
        n4 = [ rapid_ast.TypeDefAST("LOCAL", n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, n4, [], [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        with open(whoami()+".1"+".rapid","wt") as f:
            rewrite = browse_rapid_ast.WriteRapid(f)
            rewrite.visit(res)
            
        with open(whoami()+".2"+".rapid","wt") as f:
            f.write(text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing RECORD")
        


            

    
if __name__ == '__main__':
    unittest.main()