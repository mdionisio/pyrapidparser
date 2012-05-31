import unittest
import rapid_ast
import browse_rapid_ast


# functions
def whoami():
    import inspect
    return inspect.stack()[1][3]
    
    
def writerapidfile(testname, ast, text):
    with open(testname+".ast."+".rapid","wt") as f:
        rewrite = browse_rapid_ast.WriteRapid(f)
        rewrite.visit(ast)
        
    with open(testname+".source."+".rapid","wt") as f:
        f.write(text)


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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

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
        
        writerapidfile(whoami(), res, text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing RECORD")
        
    def test_rapid_declaration_1(self):
        text = r"""
MODULE syun1
    VAR num a := 1;
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("num")
        n8 = rapid_ast.IdentifierAST("a")
        n11 = rapid_ast.LiteralATS(1)
        n10 = rapid_ast.ExpressionAST(n11)
        n9 = rapid_ast.ConstExpressionAST(n10)
        n7 = rapid_ast.VarDefinitionAST(n8, n9, [])
        n5 = rapid_ast.VarDeclarationAST(n6, n7)
        n4 = [ rapid_ast.DataDefATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], n4, [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        self.assertTrue(compare.full_compare(res,n3), "there is error parsing declaration with literal")
        
    def test_rapid_declaration_2(self):
        text = r"""
MODULE syun1
    CONST num a := 1 + 3;
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("num")
        n8 = rapid_ast.IdentifierAST("a")
        n13 = rapid_ast.LiteralATS(1)
        n12 = rapid_ast.LiteralATS(3)
        n11 = rapid_ast.Operator2AST('+', n12, n13)
        n10 = rapid_ast.ExpressionAST(n11)
        n9 = rapid_ast.ConstExpressionAST(n10)
        n7 = rapid_ast.VarDefinitionAST(n8, n9, [])
        n5 = rapid_ast.ConstDeclarationAST(n6, n7)
        n4 = [ rapid_ast.DataDefATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], n4, [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing declaration with +")
        
    def test_rapid_declaration_3(self):
        text = r"""
MODULE syun1
    PERS num a{3} := [ 1, 2, 3 ];
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("num")
        n8 = rapid_ast.IdentifierAST("a")
        n12 = [ rapid_ast.LiteralATS(1), rapid_ast.LiteralATS(2), rapid_ast.LiteralATS(3) ]
        n11 = rapid_ast.AggregateAST(n12)
        n10 = rapid_ast.ExpressionAST(n11)
        n9 = rapid_ast.ConstExpressionAST(n10)
        n22 = rapid_ast.LiteralATS(3)
        n21 = rapid_ast.ExpressionAST(n22)
        n20 = [ rapid_ast.ConstExpressionAST(n21) ]
        n7 = rapid_ast.VarDefinitionAST(n8, n9, n20)
        n5 = rapid_ast.PersDeclarationAST(n6, n7)
        n4 = [ rapid_ast.DataDefATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], n4, [])
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing declaration with vector")
        
    def test_rapid_proc_declaration_1(self):
        text = r"""
MODULE syun1
    PROC pippo ()
    ENDPROC
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("pippo")
        n5 = rapid_ast.ProcedureDeclarationAST(n6, [], [], [], None, None, None)
        n4 = [ rapid_ast.RoutineDeclarationATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], n4)
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing proc declaration")
        
    def test_rapid_proc_declaration_2(self):
        text = r"""
MODULE syun1
    PROC pippo (VAR num a1)
    ENDPROC
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n8 = rapid_ast.IdentifierAST("num")
        n9 = rapid_ast.IdentifierAST("a1")
        n7 = [ rapid_ast.ParameterDefinitionAST("VAR", n8, n9, 0) ]
        n6 = rapid_ast.IdentifierAST("pippo")
        n5 = rapid_ast.ProcedureDeclarationAST(n6, n7, [], [], None, None, None)
        n4 = [ rapid_ast.RoutineDeclarationATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], n4)
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing proc declaration with parameter")
        
    def test_rapid_proc_declaration_3(self):
        text = r"""
MODULE syun1
    PROC pippo ()
        a := 1;
    ENDPROC
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n12 = rapid_ast.IdentifierAST("a")
        n9 = rapid_ast.VariableAST(n12, [], None)
        n11 = rapid_ast.LiteralATS(1)
        n10 = rapid_ast.ExpressionAST(n11)
        n8 = rapid_ast.AssignmentStatementAST(n9, n10)
        n7 = [ rapid_ast.StatementAST(n8) ]
        n6 = rapid_ast.IdentifierAST("pippo")
        n5 = rapid_ast.ProcedureDeclarationAST(n6, [], [], n7, None, None, None)
        n4 = [ rapid_ast.RoutineDeclarationATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], n4)
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)
        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing proc declaration with stantment")
        
    def test_rapid_func_declaration_1(self):
        text = r"""
MODULE syun1
    FUNC num pippo ()
    ENDFUNC
ENDMODULE
"""
        res = TestParserFunctions.parser.parse(text, 'file.rapid', debuglevel=0)  
  
        n1 = []
        n2 = rapid_ast.IdentifierAST("syun1")
        n6 = rapid_ast.IdentifierAST("pippo")
        n7 = rapid_ast.IdentifierAST("num")
        n5 = rapid_ast.FunctionDeclarationAST(n7, n6, [], [], [], None, None, None)
        n4 = [ rapid_ast.RoutineDeclarationATS(None, n5) ]
        n3 = rapid_ast.ModuleAST(n2, n1, [], [], n4)
        
        compare = browse_rapid_ast.CompareRapid()
        
        writerapidfile(whoami(), res, text)

        
        self.assertTrue(compare.full_compare(res,n3), "there is error parsing func declaration")
        


            

    
if __name__ == '__main__':
    unittest.main()