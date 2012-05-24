import unittest
import rapid_ast
import brawse_rapid_ast


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
  
        n1 = rapid_ast.ModuleAttributeAST([])
        n2 = rapid_ast.IdentifierAST("syun1")
        n3 = rapid_ast.ModuleAST(n1, n2, [], [], [])
        
        compare = brawse_rapid_ast.CompareRapid()

        self.assertTrue(compare.compare(res,n3), "there is error prsing module")
    
    
    def test_rapid_module_2(self):
        text = r"""
MODULE syun1(SYSMODULE)
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = rapid_ast.ModuleAttributeAST(["SYSMODULE"])
        n2 = rapid_ast.IdentifierAST("syun1")
        n3 = rapid_ast.ModuleAST(n1, n2, [], [], [])
        
        compare = brawse_rapid_ast.CompareRapid()

        self.assertTrue(compare.compare(res,n3), "there is error prsing module")
            

    
if __name__ == '__main__':
    unittest.main()