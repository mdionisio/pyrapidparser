#------------------------------------------------------------------------------
# pycparser: c_parser.py
#
# CParser class: Parser and AST builder for the C language
#
# Copyright (C) 2008-2012, Eli Bendersky
# License: BSD
#------------------------------------------------------------------------------
import re

import ply.yacc

import rapid_ast
from rapid_lexer import RAPIDLexer
from plyparser import PLYParser, Coord, ParseError


class RAPIDParser(PLYParser):    
    def __init__(
            self, 
            lex_optimize=True,
            lextab='pyRAPIDparser.lextab',
            yacc_optimize=True,
            yacctab='pyRAPIDparser.yacctab',
            yacc_debug=False):
        """ Create a new RAPIDParser.
        
            Some arguments for controlling the debug/optimization
            level of the parser are provided. The defaults are 
            tuned for release/performance mode. 
            The simple rules for using them are:
            *) When tweaking CParser/CLexer, set these to False
            *) When releasing a stable parser, set to True
            
            lex_optimize:
                Set to False when you're modifying the lexer.
                Otherwise, changes in the lexer won't be used, if
                some lextab.py file exists.
                When releasing with a stable lexer, set to True
                to save the re-generation of the lexer table on 
                each run.
            
            lextab:
                Points to the lex table that's used for optimized
                mode. Only if you're modifying the lexer and want
                some tests to avoid re-generating the table, make 
                this point to a local lex table file (that's been
                earlier generated with lex_optimize=True)
            
            yacc_optimize:
                Set to False when you're modifying the parser.
                Otherwise, changes in the parser won't be used, if
                some parsetab.py file exists.
                When releasing with a stable parser, set to True
                to save the re-generation of the parser table on 
                each run.
            
            yacctab:
                Points to the yacc table that's used for optimized
                mode. Only if you're modifying the parser, make 
                this point to a local yacc table file
                        
            yacc_debug:
                Generate a parser.out file that explains how yacc
                built the parsing table from the grammar.
        """
        self.rapidlex = RAPIDLexer( error_func=self._lex_error_func )
            
        self.rapidlex.build(
            optimize=lex_optimize,
            lextab=lextab)
        self.tokens = self.rapidlex.tokens
        
        self.rapidparser = ply.yacc.yacc(
            module=self, 
            start='module_declaration',
            debug=yacc_debug,
            optimize=yacc_optimize,
            tabmodule=yacctab)
        
        # Stack of scopes for keeping track of typedefs. _scope_stack[-1] is
        # the current (topmost) scope.
        #
        self._scope_stack = [set()]
    
    def parse(self, text, filename='', debuglevel=0):
        """ Parses RAPID code and returns an AST.
        
            text:
                A string containing the RAPID source code
            
            filename:
                Name of the file being parsed (for meaningful
                error messages)
            
            debuglevel:
                Debug level to yacc
        """
        self.rapidlex.filename = filename
        self.rapidlex.reset_lineno()
        if not text or text.isspace():
            #return rapid_ast.FileAST([])
            return None
        else:
            return self.rapidparser.parse(text, lexer=self.rapidlex, debug=debuglevel)
    

    def _lex_error_func(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column))
        
    ##
    ## Grammar productions
    ##
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Identifiers.    par:2.3
    ###

    def p_identifier_1(self, p):
        """ identifier    : ID
        """
        p[0] = rapid_ast.IdentifierAST( p[1], self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Identifiers.    par:2.3
    ###
    def p_identifier_2(self, p):
        """ identifier    : PLACEHOLDER_ID
        """
        p[0] = rapid_ast.IdentifierAST( None, self._coord(p.lineno(1)) )

    
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Task Modules.    par:9.1
    ###
    
    
    def p_module_declaration_1(self, p):
        """ module_declaration    : MODULE module_name type_definition_list data_definition_list routine_definition_list ENDMODULE
        """
        p[0] = rapid_ast.ModuleAST(p[2], [], p[3], p[4],p[5], self._coord(p.lineno(1)))
        
    ##
    ## Grammar productions
    ##
    def p_module_declaration_2(self, p):
        """ module_declaration    : MODULE module_name LPAREN module_attributelist RPAREN type_definition_list data_definition_list routine_definition_list  ENDMODULE
        """
        p[0] = rapid_ast.ModuleAST(p[2], p[4], p[6], p[7], p[8], self._coord(p.lineno(1)))
        #p[0] = rapid_ast.FileAST(p[1])
        
    def p_module_name(self, p):
        """ module_name    :  identifier 
        """
        p[0] = p[1]
    
    def p_module_attributelist(self, p):
        """ module_attributelist    : module_attribute
                                                | module_attributelist COMMA module_attribute
        """
        if len(p)==2:
            p[0] = [ p[1] ]
        else:
            attriblist = p[1]
            attriblist.append(p[3])
            p[0] = attriblist
        
    def p_module_attribute(self, p):
        """ module_attribute         : SYSMODULE
                                                | NOVIEW
                                                | NOSTEPIN
                                                | VIEWONLY
                                                | READONLY
        """
        p[0] = rapid_ast.ModuleAttributeAST(p[1], self._coord(p.lineno(1)) )
        
    def p_type_definition_list(self, p):
        """ type_definition_list         : 
                                                     | type_definition_list type_definition
        """
        if len(p)==1:
            p[0] = []
        else:
            attriblist = p[1]
            attriblist.append(p[2])
            p[0] = attriblist
        
    def p_data_definition_list(self, p):
        """ data_definition_list         : 
        """
        #todo
        p[0] = []
        
    def p_routine_definition_list(self, p):
        """ routine_definition_list         : 
                                                     | routine_definition_list data_definition
        """
        if len(p)==1:
            p[0] = []
        else:
            attriblist = p[1]
            attriblist.append(p[2])
            p[0] = attriblist
            
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Declaration.    par:2.18
    ###
    def p_routine_definition_list_1(self, p):
        """ data_definition         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], self._coord(p.lineno(1)))
        
    def p_routine_definition_list_2(self, p):
        """ data_definition         : PLACEHOLDER_DDN
        """
        p[0] = rapid_ast.DataDefATS(None, None, self._coord(p.lineno(1)))
        
    def p_routine_definition_list_3(self, p):
        """ data_definition         : variable_definition
                                             | LOCAL variable_definition
        """
        if len(p)==2:
            p[0] = rapid_ast.DataDefATS( None, p[1], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.DataDefATS( "LOCAL", p[2], self._coord(p.lineno(1)))
            
    def p_routine_definition_list_4(self, p):
        """ data_definition         : persistent_definition
                                             | LOCAL persistent_definition
        """
        if len(p)==2:
            p[0] = rapid_ast.DataDefATS( None, p[1], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.DataDefATS( "LOCAL", p[2], self._coord(p.lineno(1)))
            
    def p_routine_definition_list_5(self, p):
        """ data_definition         : constant_definition
                                             | LOCAL constant_definition
        """
        if len(p)==2:
            p[0] = rapid_ast.DataDefATS( None, p[1], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.DataDefATS( "LOCAL", p[2], self._coord(p.lineno(1)))
            
    def p_routine_definition_list_5(self, p):
        """ data_definition         : TASK persistent_definition
        """
        p[0] = rapid_ast.DataDefATS( "TASK", p[1], self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Variable declarations.    par:2.22
    ###
    def p_variable_definition(self, p):
        """ variable_definition         : VAR data_type variable_instance SEMI
        """
        p[0] = rapid_ast.VarDefinitionAST(p[2], p[3], self._coord(p.lineno(1)))
        
    def p_variable_instance_1(self, p):
        """ variable_instance         : identifier
                                                | identifier EQUALS constant_expression
        """
        if len(p)==2:
            p[0] = rapid_ast.VarInstanceAST(p[1], None, [], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.VarInstanceAST(p[1], p[3], [], self._coord(p.lineno(1)))
        
    def p_variable_instance_2(self, p):
        """ variable_instance         : identifier LBRACE dim_list RBRACE
                                                | identifier LBRACE dim_list RBRACE EQUALS constant_expression
        """
        if len(p)==5:
            p[0] = rapid_ast.VarInstanceAST(p[1], None, p[3], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.VarInstanceAST(p[1], p[6], p[3], self._coord(p.lineno(1)))
        
    def p_dim_list(self, p):
        """ dim_list         : dim
                                  | dim_list dim
        """
        if len(p)==2:
            p[0] = [ p[1] ]
        else:
            attriblist = p[1]
            attriblist.append(p[2])
            p[0] = attriblist
            
        
    def p_dim(self, p):
        """ dim         : constant_expression
        """
        p[0] = p[1]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Expressions.    par:3
    ###
        
    def p_expression_1(self, p):
        """ expression         : expr
        """
        p[0] = rapid_ast.ExpressionAST(p[1], self._coord(p.lineno(1)))
        
    def p_expression_2(self, p):
        """ expression         : PLACEHOLDER_EXP
        """
        p[0] = rapid_ast.ExpressionAST(None, self._coord(p.lineno(1)))
        
    def p_expr(self, p):
        """ expr         : NOT logical_term_list
                             | logical_term_list
        """
        if len(p)==2:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator1AST("NOT", p[2])
        
    def p_logical_term_list(self, p):
        """ logical_term_list         : logical_term
                                               | logical_term OR logical_term_list
                                               | logical_term XOR logical_term_list
        """
        if len(p)==2:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], self._coord(p.lineno(1)))
        
    def p_logical_term(self, p):
        """ logical_term         : relation_list
        """
        p[0] = p[1]
        
    def p_relation_list(self, p):
        """ relation_list         : relation
                                        | relation AND relation_list
        """
        if len(p)==2:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], self._coord(p.lineno(1)))
        
    def p_relation(self, p):
        """ relation         : simple_expr
                                  | simple_expr relop simple_expr
        """
        if len(p)==2:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], self._coord(p.lineno(1)))
    
    def p_simple_expr(self, p):
        """ simple_expr         : addop term simple_expr_list
                                        | term simple_expr_list
        """
        if len(p)==3:
            term = p[1]
            simple_expr_list = p[2]
        else:
            term = rapid_ast.Operator1AST(p[1], p[2], self._coord(p.lineno(1)))
            simple_expr_list = p[3]
            
        if simple_expr_list is None:
            p[0] = term
        else:
            p[0] = rapid_ast.Operator2AST(simple_expr_list[0], term, simple_expr_list[1], self._coord(p.lineno(1)))
        
    def p_simple_expr_list(self, p):
        """ simple_expr_list         :  
                                              | addop term simple_expr_list
        """
        if len(p)==1:
            p[0] = None
        else:
            if p[3] is None:
                p[0] = [ ( p[1], p[2] ) ]
            else:
                p[0] = [ ( p[1], rapid_ast.Operator2AST(p[3][0], p[2], p[3][1], self._coord(p.lineno(1))) ) ]
        
    def p_term(self, p):
        """ term         : primary primary_list
        """
        if p[2] is None:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator2AST(p[2][0], p[1], p[2][1], self._coord(p.lineno(1)))
        
        
    def p_primary_list(self, p):
        """ primary_list         : 
                                        | mulop primary primary_list
        """
        if len(p)==1:
            p[0] = None
        else:
            if p[3] is None:
                p[0] = [ ( p[1], p[2] ) ]
            else:
                p[0] = [ ( p[1], rapid_ast.Operator2AST(p[3][0], p[2], p[3][1], self._coord(p.lineno(1))) ) ]         
        
    def p_primary_1(self, p):
        """ primary         : literal
        """
        p[0] = p[1]        
        
    def p_primary_2(self, p):
        """ primary         : variable
        """
        pass        
        
    def p_primary_3(self, p):
        """ primary         : persistent
        """
        pass        
        
    def p_primary_4(self, p):
        """ primary         : constant
        """
        pass        
        
    def p_primary_5(self, p):
        """ primary         : parameter
        """
        pass        
        
    def p_primary_6(self, p):
        """ primary         : function_call
        """
        pass        
        
    def p_primary_7(self, p):
        """ primary         : aggregate
        """
        pass        
        
    def p_primary_8(self, p):
        """ primary         : LPAREN expr RPAREN
        """
        p[0] = p[2]
        
    def p_relop(self, p):
        """ relop         : LT
                              | GT
                              | LE
                              | GE
                              | EQ
                              | NE
        """
        p[0] = p[1]        
        
    def p_addop(self, p):
        """ addop         :  PLUS
                                |  MINUS
        """
        p[0] = p[1]
        
    def p_mulop(self, p):
        """ mulop         : TIMES
                                | DIVIDE
                                | DIV
                                | MOD
        """
        p[0] = p[1]
        
    def p_aggregate(self, p):
        """ aggregate         :  
        """
        ########### todo
        pass            
        
    def p_function_call(self, p):
        """ function_call         :  
        """
        ########### todo
        pass            
        
    def p_parameter(self, p):
        """ parameter         :  
        """
        ########### todo
        pass            
        
    def p_constant(self, p):
        """ constant         :  
        """
        ########### todo
        pass

    def p_persistent(self, p):
        """ persistent         :  
        """
        ########### todo
        pass 
        
    def p_variable(self, p):
        """ variable         :  
        """
        ########### todo
        pass 
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Literals.    par:3.4
    ###    
        
    def p_literal_1(self, p):
        """ literal         :  num_literal
        """
        p[0] = rapid_ast.LiteralATS( p[1], self._coord(p.lineno(1)) ) 
        
    def p_literal_2(self, p):
        """ literal         :  string_literal
        """
        p[0] = rapid_ast.LiteralATS( p[1], self._coord(p.lineno(1)) ) 
        
    def p_literal_3(self, p):
        """ literal         :  bool_literal
        """
        p[0] = rapid_ast.LiteralATS( p[1], self._coord(p.lineno(1)) ) 
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Num literals.    par:2.5
    ###  
        
    def p_num_literal(self, p):
        """ num_literal         :  INT_CONST_DEC
                                        |  FLOAT_CONST
        """
        p[0] = p[1]
        
    def p_string_literal(self, p):
        """ string_literal         :  STRING_LITERAL
        """
        p[0] = p[1]
        
    def p_bool_literal(self, p):
        """ bool_literal         :  TRUE
                                       | FALSE
        """
        p[0] = ( p[1]=="TRUE" )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Constant expressions.    par:3.11
    ###
        
    def p_constant_expression(self, p):
        """ constant_expression         : expression
        """
        p[0] = rapid_ast.ConstExpressionAST( p[1], self._coord(p.lineno(1)))
        
    ###
        
    def p_persistent_definition(self, p):
        """ persistent_definition         : 
        """
        pass
        
    def p_constant_definition(self, p):
        """ constant_definition         : 
        """
        pass
        
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Types.    par:2.11
    ###
    
    def p_type_definition_1(self, p):
        """ type_definition         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], self._coord(p.lineno(1)))
    
    def p_type_definition_2(self, p):
        """ type_definition         : PLACEHOLDER_TDN
        """
        p[0] = rapid_ast.TypeDefAST(None, None, self._coord(p.lineno(1)))
    
    def p_type_definition_3(self, p):
        """ type_definition         : record_definition
                                                | LOCAL record_definition
        """
        if len(p)==2:
            p[0] = rapid_ast.TypeDefAST(None, p[1], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.TypeDefAST("LOCAL", p[2], self._coord(p.lineno(1)))
        
    def p_type_definition_4(self, p):
        """ type_definition         : alias_definition
                                                | LOCAL alias_definition
        """
        if len(p)==2:
            p[0] = rapid_ast.TypeDefAST(None, p[1], self._coord(p.lineno(1)))
        else:
            p[0] = rapid_ast.TypeDefAST("LOCAL", p[2], self._coord(p.lineno(1)))
        
    
    def p_data_type(self, p):
        """ data_type         : identifier
        """
        p[0] = p[1]
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Types.    par:2.11
    ###
        
    def p_record_definition(self, p):
        """ record_definition         : RECORD identifier record_component_list ENDRECORD
        """
        p[0] = rapid_ast.RecordDefAST(p[2], p[3], self._coord(p.lineno(1)))
        
    def p_record_component_list(self, p):
        """ record_component_list         : record_component_definition
                                                         | record_component_definition record_component_list
        """
        if len(p)==2:
            p[0] =[ p[1] ]
        else:
            attriblist = p[2]
            attriblist.insert(0, p[1])
            p[0] = attriblist
        
    def p_record_component_definition(self, p):
        """ record_component_definition         : data_type record_component_name SEMI
        """
        p[0] = rapid_ast.RecordComponentDefAST(p[1], p[2], self._coord(p.lineno(1)))
        
    # this is not documented
    #
    def p_record_component_name(self, p):
        """ record_component_name         : identifier
        """
        p[0] = p[1]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Alias Types.    par:2.15
    ###
        
    def p_alias_definition(self, p):
        """ alias_definition         : ALIAS type_name identifier SEMI
        """
        p[0] = rapid_ast.AliasDefATS(p[2], p[3], self._coord(p.lineno(1)))
        
    # this is not documented
    #
    def p_type_name(self, p):
        """ type_name         : identifier
        """
        p[0] = p[1]

    # END GRAMMAR
        
    def p_error(self, p):
        if p:
            self._parse_error(
                'before: %s' % p.value, 
                self._coord(p.lineno))
        else:
            self._parse_error('At end of input', '')


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint
    import time, sys
    
    t1 = time.time()
    parser = RAPIDParser(lex_optimize=True, yacc_debug=True, yacc_optimize=False)
    sys.stdout.write("parse created: "+ str(time.time() - t1))
    
    text = r"""
MODULE syun1(SYSMODULE)
! comment
VAR string test := "pippo !pluto";
VAR num n1 := 0;
PERS pone pose1;
VAR orient o1 := [1, 0, 0, 0];
o1.q1 := -1;
LOCAL PROC init()
ENDPROC
ENDMODULE
! end comment
"""
    text = r"""
MODULE syun1 ( SYSMODULE,  READONLY)
ENDMODULE
"""

    text = r"""
MODULE <ID> ( SYSMODULE,  READONLY)
ENDMODULE
"""

    text = r"""
MODULE syun1(SYSMODULE)
! my comment
RECORD pippo
 num numero;
 string string;
ENDRECORD
ALIAS num another_num;
LOCAL ALIAS num another_num1;
ENDMODULE
"""

    text = r"""
MODULE syun1(SYSMODULE)
! my comment
RECORD pippo
 num numero;
 string string;
ENDRECORD
ALIAS num another_num;
LOCAL ALIAS num another_num1;
VAR num pippo;
ENDMODULE
"""

    text = r"""
MODULE syun1(SYSMODULE)
! my comment
RECORD pippo
 num numero;
 string string;
ENDRECORD
ALIAS num another_num;
LOCAL ALIAS num another_num1;
VAR num pippo{3};
ENDMODULE
"""

    text = r"""
MODULE syun1(SYSMODULE)
! my comment
RECORD pippo
 num numero;
 string string;
ENDRECORD
ALIAS num another_num;
LOCAL ALIAS num another_num1;
VAR num pippo := 5;
ENDMODULE
"""
    
    ## set debuglevel to 2 for debugging
    t = parser.parse(text, 'x.rapid', debuglevel=0)
    
    sys.stdout.write("end parse: "+ str(time.time() - t1))
    
    t.show(attrnames=True, nodenames=True, showcoord=True)

