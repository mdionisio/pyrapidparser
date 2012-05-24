import unittest


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
        
    def test_rapid_empty(self):
        text = r"""
MODULE syun1(SYSMODULE)
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)           
        res.show(attrnames=True, nodenames=True, showcoord=True)
        self.assertTrue(True, "there is nothing")
            

    
if __name__ == '__main__':
    unittest.main()