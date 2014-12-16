#------------------------------------------------------------------------------
# pyrapidparser: rapid_parser.py
#
# CParser class: Parser and AST builder for the RAPID language
#
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
            yacc_debug=False,
            start_from='module_declaration'):
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
            start=start_from,
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
        p[0] = rapid_ast.IdentifierAST( p[1], coord=self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Identifiers.    par:2.3
    ###
    def p_identifier_2(self, p):
        """ identifier    : PLACEHOLDER_ID
        """
        p[0] = rapid_ast.IdentifierAST( None, coord=self._coord(p.lineno(1)) )

    
    
    def p_module_declaration_list_1(self, p):
        """ module_declaration_list    : 
        """
        p[0] = rapid_ast.ModulesAST( [ ] )
        
    def p_module_declaration_list_2(self, p):
        """ module_declaration_list    :  module_declaration_list module_declaration
        """
        attriblist = p[1].module_list
        attriblist.append(p[2])
        p[0] = rapid_ast.ModulesAST(attriblist)
    
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Task Modules.    par:9.1
    ###
    
    def p_module_declaration_1(self, p):
        """ module_declaration    : MODULE identifier type_definition_list data_declaration_list routine_definition_list ENDMODULE
        """
        p[0] = rapid_ast.ModuleAST(p[2], [], p[3], p[4],p[5], coord=self._coord(p.lineno(1)))
        
    def p_module_declaration_2(self, p):
        """ module_declaration    : MODULE identifier LPAREN module_attributelist RPAREN type_definition_list data_declaration_list routine_definition_list  ENDMODULE
        """
        p[0] = rapid_ast.ModuleAST(p[2], p[4], p[6], p[7], p[8], coord=self._coord(p.lineno(1)))
    
    def p_module_attributelist_1(self, p):
        """ module_attributelist    : module_attribute
        """
        p[0] = [ p[1] ]
            
    def p_module_attributelist(self, p):
        """ module_attributelist    : module_attributelist COMMA module_attribute
        """
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
        p[0] = rapid_ast.ModuleAttributeAST(p[1], coord=self._coord(p.lineno(1)) )
        
    def p_type_definition_list_1(self, p):
        """ type_definition_list         : 
        """
        p[0] = []
        
    def p_type_definition_list_2(self, p):
        """ type_definition_list         : type_definition_list type_definition
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
                
    def p_data_declaration_list_1(self, p):
        """ data_declaration_list         : 
        """
        p[0] = [ ]
        
    def p_data_declaration_list_2(self, p):
        """ data_declaration_list         : data_declaration_list data_declaration
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
        
        
    def p_routine_definition_list_1(self, p):
        """ routine_definition_list         :
        """
        p[0] = []
            
    def p_routine_definition_list_2(self, p):
        """ routine_definition_list         : routine_definition_list routine_declaration
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
        
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Routine Declaration.    par:5
    ###
            
    def p_routine_declaration_1(self, p):
        """ routine_declaration         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], coord=self._coord(p.lineno(1)))
        
    def p_routine_declaration_2(self, p):
        """ routine_declaration         : PLACEHOLDER_RDN
        """
        p[0] =  rapid_ast.RoutineDeclarationATS(None, None, coord=self._coord(p.lineno(1)))
        
    def p_routine_declaration_3(self, p):
        """ routine_declaration         : procedure_declaration
                                                    | function_declaration
                                                    | trap_declaration
        """
        p[0] =  p[1]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Parameter declarations.    par:5.1
    ###
    
    def p_parameter_list_1(self, p):
        """ parameter_list         : 
        """
        p[0] = [  ]
        
    def p_parameter_list_2(self, p):
        """ parameter_list         : first_parameter_declaration
        """
        p[0] = [ p[1] ]
    
    def p_parameter_list_3(self, p):
        """ parameter_list         : first_parameter_declaration next_parameter_declaration_list
        """
        attriblist = p[2]
        attriblist.insert(0, p[1])
        p[0] = attriblist
    
    
    def p_next_parameter_declaration_list_1(self, p):
        """ next_parameter_declaration_list         : next_parameter_declaration 
        """
        p[0] = [ p[1] ]
        
    def p_next_parameter_declaration_list_2(self, p):
        """ next_parameter_declaration_list         : next_parameter_declaration next_parameter_declaration_list
        """
        attriblist = p[2]
        attriblist.insert(0, p[1])
        p[0] = attriblist
        
    def p_next_parameter_declaration_1(self, p):
        """ next_parameter_declaration         : COMMA parameter_declaration
        """
        p[0] = p[2]
        
    def p_next_parameter_declaration_2(self, p):
        """ next_parameter_declaration         : COMMA optional_parameter_declaration
        """
        p[0] = p[2]
        
    def p_next_parameter_declaration_3(self, p):
        """ next_parameter_declaration         : optional_parameter_declaration
        """
        p[0] = p[1]
        
    def p_next_parameter_declaration_4(self, p):
        """ next_parameter_declaration         : COMMA PLACEHOLDER_PAR
        """
        p[0] = p[1]
        
    def p_first_parameter_declaration_1(self, p):
        """ first_parameter_declaration         : parameter_declaration
        """
        p[0] = p[1]
        
    def p_first_parameter_declaration_2(self, p):
        """ first_parameter_declaration         : optional_parameter_declaration
        """
        p[0] = p[1]
        
    def p_first_parameter_declaration_3(self, p):
        """ first_parameter_declaration         : PLACEHOLDER_PAR
        """
        p[0] = None  #todo
    
    def p_optional_parameter_declaration_1(self, p):
        """ optional_parameter_declaration         : CONSLASH parameter_declaration parameter_declaration_alternative_list
        """
        p[0] = rapid_ast.OptionalParameterDefinitionAST(p[2], p[3], coord=self._coord(p.lineno(1)))   
        
    def p_optional_parameter_declaration_2(self, p):
        """ optional_parameter_declaration         : CONSLASH PLACEHOLDER_ALT parameter_declaration_alternative_list
        """
        p[0] = rapid_ast.OptionalParameterDefinitionAST(None, p[3], coord=self._coord(p.lineno(1)))
        
    def p_parameter_declaration_alternative_list_1(self, p):
        """ parameter_declaration_alternative_list         : 
        """
        p[0] = []
        
    def p_parameter_declaration_alternative_list_2(self, p):
        """ parameter_declaration_alternative_list         : PIPE parameter_declaration parameter_declaration_alternative_list
        """
        attriblist = p[3]
        attriblist.insert(0, p[2])
        p[0] = attriblist
        
    def p_parameter_declaration_alternative_list_3(self, p):
        """ parameter_declaration_alternative_list         : PIPE PLACEHOLDER_ALT parameter_declaration_alternative_list
        """
        attriblist = p[3]
        attriblist.insert(0, None)          #todo
        p[0] = attriblist
        
    def p_parameter_declaration_1(self, p):
        """ parameter_declaration         : var_type identifier identifier 
        """
        p[0] = rapid_ast.ParameterDefinitionAST(p[1], p[2], p[3], 0, coord=None)
        
    def p_parameter_declaration_2(self, p):
        """ parameter_declaration         : var_type identifier identifier LBRACE parameter_size RBRACE
        """
        p[0] = rapid_ast.ParameterDefinitionAST(p[1], p[2], p[3], len(p[5]), coord=None)
        
    def p_parameter_declaration_3(self, p):
        """ parameter_declaration         : var_type identifier identifier LBRACE PLACEHOLDER_DIM RBRACE
        """
        p[0] = rapid_ast.ParameterDefinitionAST(p[1], p[2], p[3], None, coord=None)
        
    def p_parameter_declaration_4(self, p):
        """ parameter_declaration         : switch identifier 
        """
        p[0] = rapid_ast.SwitchParameterDefinitionAST(p[2], coord=self._coord(p.lineno(1)))
        
    def p_parameter_size_1(self, p):
        """ parameter_size         : TIMES
        """
        p[0] = [ '*' ]
        
    def p_parameter_size_2(self, p):
        """ parameter_size         : TIMES COMMA parameter_size
        """
        attriblist = p[3]
        attriblist.insert(0, '*')
        p[0] = attriblist
        
    def p_var_type_1(self, p):
        """ var_type         : VAR
                                    | PERS
                                    | INOUT
        """
        p[0] = p[1]
        
    def p_var_type_2(self, p):
        """ var_type         : 
        """
        p[0] = "NORMAL"
   
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Procedure declarations.    par:5.3
    ###
        
    def p_procedure_declaration_1(self, p):
        """ procedure_declaration         : PROC identifier LPAREN parameter_list RPAREN data_declaration_list statement_list routine_backward routine_error routine_undo ENDPROC
        """
        p[0] = rapid_ast.RoutineDeclarationATS(None, rapid_ast.ProcedureDeclarationAST(p[2], p[4], p[6], p[7], p[8], p[9], p[10], coord=self._coord(p.lineno(1))), coord=None)
        
    def p_procedure_declaration_2(self, p):
        """ procedure_declaration         : LOCAL_PROC identifier LPAREN parameter_list RPAREN data_declaration_list statement_list routine_backward routine_error routine_undo ENDPROC
        """
        p[0] = rapid_ast.RoutineDeclarationATS("LOCAL", rapid_ast.ProcedureDeclarationAST(p[2], p[4], p[6], p[7], p[8], p[9], p[10], coord=self._coord(p.lineno(1))), coord=None)
                        
    def p_routine_backward_1(self, p):
        """ routine_backward         : 
        """
        p[0] = None
        
    def p_routine_backward_2(self, p):
        """ routine_backward         : BACKWARD statement_list
        """
        p[0] = rapid_ast.RoutineBackwardAST(p[2], coord=self._coord(p.lineno(1)))
        
        
    def p_routine_error_1(self, p):
        """ routine_error         : 
        """
        p[0] = None
    
    def p_routine_error_2(self, p):
        """ routine_error         : ERROR LPAREN error_number_list RPAREN statement_list
        """
        p[0] = rapid_ast.RoutineErrorAST(p[2], p[3], coord=self._coord(p.lineno(1)))
        
    def p_routine_error_3(self, p):
        """ routine_error         : ERROR statement_list
        """
        p[0] = rapid_ast.RoutineErrorAST([], p[2], coord=self._coord(p.lineno(1)))   
        
    def p_error_number_list_1(self, p):
        """ error_number_list         : error_number
        """
        p[0] = [ p[1] ]
        
    def p_error_number_list_2(self, p):
        """ error_number_list         : error_number COMMA error_number_list
        """
        attriblist = p[3]
        attriblist.insert(0, p[1])
        p[0] = attriblist
        
    def p_error_number(self, p):
        """ error_number         : num_literal
                                            | identifier
        """
        p[0] = p[1]
        
    def p_routine_undo_1(self, p):
        """ routine_undo         : 
        """
        p[0] = None
        
    def p_routine_undo_2(self, p):
        """ routine_undo         : UNDO statement_list
        """
        p[0] = rapid_ast.RoutineUndoAST(p[2], coord=self._coord(p.lineno(1)))
    
    def p_function_declaration_1(self, p):
        """ function_declaration         : FUNC identifier identifier LPAREN parameter_list RPAREN data_declaration_list statement_list routine_error routine_undo ENDFUNC
        """  
        p[0] = rapid_ast.RoutineDeclarationATS(None, rapid_ast.FunctionDeclarationAST(p[2], p[3], p[5], p[7], p[8], p[9], p[10], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_function_declaration_2(self, p):
        """ function_declaration         : LOCAL_FUNC identifier identifier LPAREN parameter_list RPAREN data_declaration_list statement_list routine_error routine_undo ENDFUNC
        """  
        p[0] = rapid_ast.RoutineDeclarationATS("LOCAL", rapid_ast.FunctionDeclarationAST(p[2], p[3], p[5], p[7], p[8], p[9], p[10], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_trap_declaration_1(self, p):
        """ trap_declaration         : TRAP identifier data_declaration_list statement_list routine_error routine_undo ENDTRAP
        """   
        p[0] = rapid_ast.RoutineDeclarationATS(None, rapid_ast.TrapDeclarationAST(p[2], p[3], p[4], p[5], p[6], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_trap_declaration_2(self, p):
        """ trap_declaration         : LOCAL_TRAP identifier data_declaration_list statement_list routine_error routine_undo ENDTRAP
        """   
        p[0] = rapid_ast.RoutineDeclarationATS("LOCAL", rapid_ast.TrapDeclarationAST(p[2], p[3], p[4], p[5], p[6], coord=self._coord(p.lineno(1))), coord=None);
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Statement Lists.    par:4.2
    ###
        
    def p_statement_list_1(self, p):
        """ statement_list         : 
        """
        p[0] = [ ]
        
    def p_statement_list_2(self, p):
        """ statement_list         : statement_list statement 
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Statements.    par:4
    ###
    
    def p_statement_1(self, p):
        """ statement         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], coord=self._coord(p.lineno(1)))
        
    def p_statement_2(self, p):
        """ statement         : single_statement
                                      | compound_statement
                                      | label
        """
        p[0] = rapid_ast.StatementAST(p[1], coord=None)
        
    def p_statement_3(self, p): 
        """ statement         : PLACEHOLDER_SMT
        """
        p[0] = rapid_ast.StatementAST(None, coord=self._coord(p.lineno(1)))
        
    def p_single_statement(self, p): 
        """ single_statement         :  assignment_statement
                                                    | procedure_call
                                                    | goto_statement
                                                    | return_statement
                                                    | raise_statement
                                                    | exit_statement
                                                    | retry_statement
                                                    | trynext_statement
                                                    | connect_statement
        """
        p[0] = p[1]
        
    def p_compound_statement(self, p): 
        """ compound_statement         : if_statement
                                                        | compact_if_statement
                                                        | for_statement
                                                        | while_statement
                                                        | test_statement
        """
        p[0] = p[1]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Assignment statement.    par:4.4
    ###
        
    def p_assignment_statement(self, p): 
        """ assignment_statement         : assignment_target EQUALS expression SEMI
        """
        p[0] = rapid_ast.AssignmentStatementAST(p[1], p[3], coord=None)
        
    def p_assignment_target_1(self, p): 
        """ assignment_target         : variable
        """
        p[0] = p[1]
        
    def p_assignment_target_2(self, p): 
        """ assignment_target         : PLACEHOLDER_VAR
        """
        p[0] = rapid_ast.VariableAST(None, [], None, coord=self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Procedure call.    par:4.5
    ###
        
    def p_procedure_call_1(self, p): 
        """ procedure_call         : procedure SEMI
        """
        p[0] = rapid_ast.ProcedureCallAST(p[1], [], coord=None)
        
    def p_procedure_call_2(self, p): 
        """ procedure_call         : procedure procedure_argument_list SEMI
        """
        p[0] = rapid_ast.ProcedureCallAST(p[1], p[2], coord=None)
        
    def p_procedure_1(self, p): 
        """ procedure         : identifier
        """
        p[0] = p[1]
        
    def p_procedure_2(self, p): 
        """ procedure         : PERCENT expression PERCENT
        """
        p[0] = p[2]
        
    def p_procedure_argument_list_1(self, p): 
        """ procedure_argument_list         : procedure_argument
        """
        p[0] = [ p[1] ]
        
    def p_procedure_argument_list_2(self, p):
        """ procedure_argument_list         :  procedure_argument_list COMMA procedure_argument
        """
        attriblist = p[1]
        attriblist.append(p[3])
        p[0] = attriblist
        
    def p_procedure_argument_list_3(self, p):
        """ procedure_argument_list         :  procedure_argument_list optional_procedure_argument
                                                                | procedure_argument_list conditional_procedure_argument
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
            
    def p_procedure_argument_1(self, p):
        """ procedure_argument         :  required_procedure_argument
                                                    | optional_procedure_argument
                                                    | conditional_procedure_argument
        """
        p[0] = p[1]
        
    def p_procedure_argument_2(self, p):
        """ procedure_argument         :  PLACEHOLDER_ARG
        """
        p[0] = rapid_ast.ProcedureArgumentAST(None, None, None, coord=self._coord(p.lineno(1)))
        
    def p_required_procedure_argument_1(self, p):
        """ required_procedure_argument         :  identifier EQUALS expr
        """
        p[0] = rapid_ast.ProcedureArgumentAST("Required", p[1], p[3], coord=None)
        
    def p_required_procedure_argument_2(self, p):
        """ required_procedure_argument         : expr
        """
        p[0] = rapid_ast.ProcedureArgumentAST("Required", None, p[1], coord=None)
        
    def p_optional_procedure_argument_1(self, p):
        """ optional_procedure_argument         :  CONSLASH identifier EQUALS expr
        """
        p[0] = rapid_ast.ProcedureArgumentAST("Optional", p[2], p[4], coord=self._coord(p.lineno(1)))
        
    def p_optional_procedure_argument_2(self, p):
        """ optional_procedure_argument         :  CONSLASH identifier
        """
        p[0] = rapid_ast.ProcedureArgumentAST("Optional", p[2], None, coord=self._coord(p.lineno(1)))
    
    def p_conditional_procedure_argument(self, p):
        """ conditional_procedure_argument         :  CONSLASH identifier CONDOP variable
        """
        p[0] = rapid_ast.ProcedureArgumentAST("Conditional", p[2], p[4], coord=self._coord(p.lineno(1)))
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Goto Statement.    par:4.6
    ###
        
    def p_goto_statement(self, p): 
        """ goto_statement         : GOTO identifier SEMI
        """
        p[0] = rapid_ast.GotoStatementAST(p[2], coord=self._coord(p.lineno(1)))
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Return Statement.    par:4.7
    ###
        
    def p_return_statement_1(self, p): 
        """ return_statement         : RETURN SEMI
        """
        p[0] = rapid_ast.ReturnStatementAST(None, coord=self._coord(p.lineno(1)))
        
    def p_return_statement_2(self, p): 
        """ return_statement         : RETURN expression SEMI
        """
        p[0] = rapid_ast.ReturnStatementAST(p[2], coord=self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Raise Statement.    par:4.8
    ###
        
    def p_raise_statement_1(self, p): 
        """ raise_statement         : RAISE SEMI
        """
        p[0] = rapid_ast.RaiseStatementAST(None, coord=self._coord(p.lineno(1)))
        
    def p_raise_statement_2(self, p): 
        """ raise_statement         : RAISE error_number SEMI
        """
        p[0] = rapid_ast.RaiseStatementAST(p[2], coord=self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Exit Statement.    par:4.9
    ###
    
    def p_exit_statement(self, p): 
        """ exit_statement         : EXIT SEMI
        """
        p[0] = rapid_ast.ExitStatementAST(coord=self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Retry Statement.    par:4.10
    ###
        
    def p_retry_statement(self, p): 
        """ retry_statement         : RETRY SEMI
        """
        p[0] = rapid_ast.RetryStatementAST(coord=self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  TryNext Statement.    par:4.11
    ###
        
    def p_trynext_statement(self, p): 
        """ trynext_statement         : TRYNEXT SEMI
        """
        p[0] = rapid_ast.TrynextStatementAST(coord=self._coord(p.lineno(1)))
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Connect Statement.    par:4.12
    ###
        
    def p_connect_statement(self, p): 
        """ connect_statement         : CONNECT connect_taget WITH identifier SEMI
        """
        p[0] = rapid_ast.ConnectStatementAST(p[2], p[4], coord=self._coord(p.lineno(1)))
        
    def p_connect_taget_1(self, p): 
        """ connect_taget         : variable
        """
        p[0] = p[1]
        
    def p_connect_taget_2(self, p): 
        """ connect_taget         : PLACEHOLDER_VAR
        """
        p[0] = rapid_ast.VariableAST(None, [], None, coord=self._coord(p.lineno(1)) )

    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  If Statement.    par:4.13
    ###
        
    def p_if_statement_1(self, p): 
        """ if_statement         :  IF conditional_expression THEN statement_list else_statement ENDIF
        """
        p[0] = rapid_ast.IfStatement(p[2], p[4], [], p[5], coord=self._coord(p.lineno(1)) )
        
    def p_if_statement_2(self, p): 
        """ if_statement         :  IF conditional_expression THEN statement_list elseif_statement_list else_statement ENDIF
        """
        p[0] = rapid_ast.IfStatement(p[2], p[4], p[5], p[6], coord=self._coord(p.lineno(1)) )
        
    def p_conditional_expression(self, p): 
        """ conditional_expression         :  expression
        """
        p[0] = p[1]
        
    def p_elseif_statement_list_1(self, p): 
        """ elseif_statement_list         :  elseif_statement
        """
        p[0] = [ p[1] ]
        
    def p_elseif_statement_list_2(self, p): 
        """ elseif_statement_list         :  elseif_statement elseif_statement_list
        """
        attriblist = p[2]
        attriblist.insert(0, p[1])
        p[0] = attriblist
        
    def p_elseif_statement_1(self, p): 
        """ elseif_statement         :  ELSEIF conditional_expression THEN statement_list
        """
        p[0] = rapid_ast.ElseIfStatement(p[2], p[4], coord=self._coord(p.lineno(1)) )
        
    def p_elseif_statement_2(self, p): 
        """ elseif_statement         :  PLACEHOLDER_EIT
        """
        p[0] = rapid_ast.ElseIfStatement(None, None, coord=self._coord(p.lineno(1)) )
        
    def p_else_statement_1(self, p): 
        """ else_statement         :  
        """
        p[0] = []
        
    def p_else_statement_2(self, p): 
        """ else_statement         :  ELSE statement_list
        """
        p[0] = p[2]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Compact if Statement.    par:4.14
    ###
        
    def p_compact_if_statement_1(self, p): 
        """ compact_if_statement         : IF conditional_expression single_statement
        """
        p[0] = rapid_ast.IfStatement(p[2], [ p[3] ], [], [], coord=self._coord(p.lineno(1)) )
        
    def p_compact_if_statement_2(self, p): 
        """ compact_if_statement         : IF conditional_expression PLACEHOLDER_SMT
        """
        single = rapid_ast.StatementAST(None, coord=self._coord(p.lineno(1)))
        p[0] = rapid_ast.IfStatement(p[2], [ single ], [], [], coord=self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  For Statement.    par:4.15
    ###
        
    def p_for_statement_1(self, p): 
        """ for_statement        : FOR identifier FROM expression TO expression STEP expression DO statement_list ENDFOR
        """
        p[0] = rapid_ast.ForStatement(p[2], p[4], p[6], p[8], p[10], coord=self._coord(p.lineno(1)) )
        
    def p_for_statement_2(self, p): 
        """ for_statement        : FOR identifier FROM expression TO expression DO statement_list ENDFOR
        """
        step = 1
        literal_step = rapid_ast.LiteralATS( step ) 
        expression_step = rapid_ast.ExpressionAST(literal_step)
        p[0] = rapid_ast.ForStatement(p[2], p[4], p[6], expression_step, p[8], coord=self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  While Statement.    par:4.16
    ###
        
    def p_while_statement(self, p): 
        """ while_statement        : WHILE conditional_expression DO statement_list ENDWHILE
        """
        p[0] = rapid_ast.WhileStatement(p[2], p[4], coord=self._coord(p.lineno(1)) )
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Test Statement.    par:4.17
    ###
        
    def p_test_statement(self, p): 
        """ test_statement        :  TEST expression casestatement_list defaultstatement ENDTEST
        """
        p[0] = rapid_ast.TestStatement(p[2], p[3], p[4], coord=self._coord(p.lineno(1)) )
        
    def p_casestatement_list_1(self, p): 
        """ casestatement_list        :  
        """
        p[0] = [ ]
        
    def p_casestatement_list_2(self, p): 
        """ casestatement_list        :  casestatement casestatement_list
        """
        attriblist = p[2]
        attriblist.insert(0, p[1])
        p[0] = attriblist 
        
    def p_casestatement_1(self, p): 
        """ casestatement        :  CASE test_value COLON statement_list
        """
        p[0] = rapid_ast.CaseStatement( p[2], p[4], coord=self._coord(p.lineno(1)) )
        
    def p_casestatement_2(self, p): 
        """ casestatement        :  PLACEHOLDER_CSE
        """
        p[0] = rapid_ast.CaseStatement( None, [], coord=self._coord(p.lineno(1)) )
        
    def p_defaultstatement_1(self, p): 
        """ defaultstatement : 
        """
        p[0] = [ ]
        
    def p_defaultstatement_2(self, p): 
        """ defaultstatement : DEFAULT COLON statement_list
        """
        p[0] = p[3]
        
    def p_test_value_1(self, p): 
        """ test_value : expression
        """
        p[0] = [ p[1] ]
        
    def p_test_value_2(self, p): 
        """ test_value : expression COMMA test_value
        """
        attriblist = p[3]
        attriblist.insert(0, p[1])
        p[0] = attriblist 
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Label Statement.    par:4.3
    ###
        
    def p_label(self, p): 
        """ label         : identifier COLON
        """
        p[0] = rapid_ast.LabelAST(p[1], coord=None)

            
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Declaration.    par:2.18
    ###
    
    def p_data_declaration_1(self, p):
        """ data_declaration         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], coord=self._coord(p.lineno(1)))
                
    def p_data_declaration_2(self, p):
        """ data_declaration         : PLACEHOLDER_DDN
        """
        p[0] = rapid_ast.DataDefATS(None, None, coord=self._coord(p.lineno(1)))
        
    def p_data_declaration_3(self, p):
        """ data_declaration         : variable_declaration
                                                | persistent_declaration
                                                | constant_declaration
        """
        p[0] = p[1]

    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Variable declarations.    par:2.22
    ###
    def p_variable_declaration_1(self, p):
        """ variable_declaration         : VAR identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS(None, rapid_ast.VarDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_variable_declaration_2(self, p):
        """ variable_declaration         : LOCAL_VAR identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS("LOCAL", rapid_ast.VarDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_variable_declaration_3(self, p):
        """ variable_declaration         : TASK_VAR identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS("TASK", rapid_ast.VarDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_variable_definition_1(self, p):
        """ variable_definition         : identifier
        """
        p[0] = rapid_ast.VarDefinitionAST(p[1], None, [], coord=None)
            
    def p_variable_definition_2(self, p):
        """ variable_definition         : identifier EQUALS constant_expression
        """
        p[0] = rapid_ast.VarDefinitionAST(p[1], p[3], [], coord=None)
        
    def p_variable_definition_3(self, p):
        """ variable_definition         : identifier LBRACE dim_list RBRACE
        """
        p[0] = rapid_ast.VarDefinitionAST(p[1], None, p[3], coord=None)
            
    def p_variable_definition_4(self, p):
        """ variable_definition         : identifier LBRACE dim_list RBRACE EQUALS constant_expression
        """
        p[0] = rapid_ast.VarDefinitionAST(p[1], p[6], p[3], coord=None)
        
    def p_dim_list_1(self, p):
        """ dim_list         : dim
        """
        p[0] = [ p[1] ]
            
    def p_dim_list_2(self, p):
        """ dim_list         : dim_list COMMA dim
        """
        attriblist = p[1]
        attriblist.append(p[3])
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
        p[0] = rapid_ast.ExpressionAST(p[1], coord=None)
        
    def p_expression_2(self, p):
        """ expression         : PLACEHOLDER_EXP
        """
        p[0] = rapid_ast.ExpressionAST(None, coord=self._coord(p.lineno(1)))
        
    def p_expr_1(self, p):
        """ expr         : logical_term_list
        """
        p[0] = p[1]
            
    def p_expr_2(self, p):
        """ expr         : NOT logical_term_list
        """
        p[0] = rapid_ast.Operator1AST("NOT", p[2], coord=self._coord(p.lineno(1)))
        
    def p_logical_term_list_1(self, p):
        """ logical_term_list         : logical_term
        """
        p[0] = p[1]
        
    def p_logical_term_list_2(self, p):
        """ logical_term_list         : logical_term OR logical_term_list
                                               | logical_term XOR logical_term_list
        """
        p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], coord=None)
        
    def p_logical_term(self, p):
        """ logical_term         : relation_list
        """
        p[0] = p[1]
        
    def p_relation_list_1(self, p):
        """ relation_list         : relation
        """
        p[0] = p[1]
            
    def p_relation_list_2(self, p):
        """ relation_list         : relation AND relation_list
        """
        p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], coord=None)
        
    def p_relation_1(self, p):
        """ relation         : simple_expr
        """
        p[0] = p[1]
            
    def p_relation_2(self, p):
        """ relation         : simple_expr relop simple_expr
        """
        p[0] = rapid_ast.Operator2AST(p[2], p[1], p[3], coord=None)
        
        
    def p_simple_expr_1(self, p):
        """ simple_expr         : term simple_expr_list
        """
        term = p[1]
        simple_expr_list = p[2]
            
        if simple_expr_list is None:
            p[0] = term
        else:
            p[0] = rapid_ast.Operator2AST(simple_expr_list[0], term, simple_expr_list[1], coord=None)
    
    def p_simple_expr_2(self, p):
        """ simple_expr         : addop term simple_expr_list
        """
        term = rapid_ast.Operator1AST(p[1], p[2], coord=None)
        simple_expr_list = p[3]
            
        if simple_expr_list is None:
            p[0] = term
        else:
            p[0] = rapid_ast.Operator2AST(simple_expr_list[0], term, simple_expr_list[1], coord=None)
            
    def p_simple_expr_list_1(self, p):
        """ simple_expr_list         :  
        """
        p[0] = None
        
    def p_simple_expr_list_2(self, p):
        """ simple_expr_list         :  addop term simple_expr_list
        """
        if p[3] is None:
            p[0] = ( p[1], p[2] )
        else:
            p[0] = ( p[1], rapid_ast.Operator2AST(p[3][0], p[2], p[3][1], coord=None ) )
        
    def p_term(self, p):
        """ term         : primary primary_list
        """
        if p[2] is None:
            p[0] = p[1]
        else:
            p[0] = rapid_ast.Operator2AST(p[2][0], p[1], p[2][1], coord=None)
        
    def p_primary_list_1(self, p):
        """ primary_list         : 
        """
        p[0] = None
        
    def p_primary_list_2(self, p):
        """ primary_list         : mulop primary primary_list
        """
        if p[3] is None:
            p[0] = ( p[1], p[2] )
        else:
            p[0] = ( p[1], rapid_ast.Operator2AST(p[3][0], p[2], p[3][1], coord=None) )         
        
    def p_primary_1(self, p):
        """ primary         : literal
                                    | variable
                                    | function_call
                                    | aggregate
        """
        #variable, constant, persistend and parameter are egual for parsing
        p[0] = p[1]            
        
    def p_primary_2(self, p):
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
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Aggregates.    par:3.9
    ### 
        
    def p_aggregate(self, p):
        """ aggregate         :  LBRACKET aggregate_list RBRACKET
        """
        p[0] = rapid_ast.AggregateAST(p[2], coord=None)

    def p_aggregate_list_1(self, p):
        """ aggregate_list         : expr
        """
        p[0] = [ p[1] ]
            
    def p_aggregate_list_2(self, p):
        """ aggregate_list         : expr COMMA aggregate_list
        """
        attriblist = p[3]
        attriblist.insert(0, p[1])
        p[0] = attriblist
            
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Function calls.    par:3.10
    ### 
        
    def p_function_call_1(self, p):
        """ function_call         : identifier LPAREN  RPAREN
        """
        p[0] = rapid_ast.FunctionCallAST(p[1], [], coord=None)
            
    def p_function_call_2(self, p):
        """ function_call         :  identifier LPAREN function_argument_list RPAREN
        """
        p[0] = rapid_ast.FunctionCallAST(p[1], p[3], coord=None)
        
    def p_function_argument_list_1(self, p):
        """ function_argument_list         :  function_argument 
        """
        p[0] = [ p[1] ]
            
    def p_function_argument_list_2(self, p):
        """ function_argument_list         :  function_argument_list COMMA function_argument
        """
        attriblist = p[1]
        attriblist.append(p[3])
        p[0] = attriblist    
        
    def p_function_argument_list_3(self, p):
        """ function_argument_list         :  function_argument_list optional_function_argument
                                                            | function_argument_list conditional_function_argument
        """
        attriblist = p[1]
        attriblist.append(p[2])
        p[0] = attriblist
            
    def p_function_argument(self, p):
        """ function_argument         :  required_function_argument
                                                    | optional_function_argument
                                                    | conditional_function_argument
        """
        p[0] = p[1]
        
    def p_required_function_argument_1(self, p):
        """ required_function_argument         :  identifier EQUALS expr
        """
        p[0] = rapid_ast.FunctionArgumentAST("Required", p[1], p[3], coord=None)
        
    def p_required_function_argument_2(self, p):
        """ required_function_argument         : expr
        """
        p[0] = rapid_ast.FunctionArgumentAST("Required", None, p[1], coord=None)
        
    def p_optional_function_argument_1(self, p):
        """ optional_function_argument         :  CONSLASH identifier EQUALS expr
        """
        p[0] = rapid_ast.FunctionArgumentAST("Optional", p[2], p[4], coord=self._coord(p.lineno(1)))
        
    def p_optional_function_argument_2(self, p):
        """ optional_function_argument         :  CONSLASH identifier
        """
        p[0] = rapid_ast.FunctionArgumentAST("Optional", p[2], None, coord=self._coord(p.lineno(1)))
    
    def p_conditional_function_argument(self, p):
        """ conditional_function_argument         :  CONSLASH identifier CONDOP variable
        """
        p[0] = rapid_ast.FunctionArgumentAST("Conditional", p[2], p[4], coord=self._coord(p.lineno(1)))
        
                
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Variables.    par:3.5
    ### 
        
    def p_variable_1(self, p):
        """ variable         :  identifier 
        """
        p[0] = rapid_ast.VariableAST(p[1], [], None, coord=None )
        
    def p_variable_2(self, p):
        """ variable         :  identifier LBRACE index_list RBRACE
        """
        p[0] = rapid_ast.VariableAST(p[1], p[3], None, coord=None )
        
    def p_variable_3(self, p):
        """ variable         :  variable PERIOD identifier
        """
        p[0] = rapid_ast.VariableAST(p[1], [], p[3], coord=None )
        
    def p_index_list_1(self, p):
        """ index_list         : expr
        """
        p[0] = [ p[1] ]        
            
    def p_index_list_2(self, p):
        """ index_list         : expr COMMA index_list
        """
        attriblist = p[3]
        attriblist.insert(0, p[1])
        p[0] = attriblist
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Literals.    par:3.4
    ###    
        
    def p_literal(self, p):
        """ literal         :  num_literal
                               |  string_literal
                               |  bool_literal
        """
        p[0] = p[1]
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Num literals.    par:2.5
    ###  
        
    def p_num_literal(self, p):
        """ num_literal         :  INT_CONST
                                            | INT_CONST_DEC
                                            | INT_CONST_BIN
                                            | INT_CONST_OCT
                                            | INT_CONST_HEX
                                            | FLOAT_CONST
        """
        p[0] = rapid_ast.LiteralATS( p[1], coord=self._coord(p.lineno(1)) ) 
        
    def p_string_literal(self, p):
        """ string_literal         :  STRING_LITERAL
        """
        p[0] = rapid_ast.LiteralATS( p[1], coord=self._coord(p.lineno(1)) ) 
        
    def p_bool_literal(self, p):
        """ bool_literal         :  TRUE
                                       | FALSE
        """
        p[0] = rapid_ast.LiteralATS(  p[1]=="TRUE", coord=self._coord(p.lineno(1)) ) 
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Constant expressions.    par:3.11
    ###
        
    def p_constant_expression(self, p):
        """ constant_expression         : expression
        """
        p[0] = rapid_ast.ConstExpressionAST( p[1], coord=None)
        
    ###
        
    def p_persistent_declaration_1(self, p):
        """ persistent_declaration         : PERS identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS(None, rapid_ast.PersDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_persistent_declaration_2(self, p):
        """ persistent_declaration         : LOCAL_PERS identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS("LOCAL", rapid_ast.PersDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_persistent_declaration_3(self, p):
        """ persistent_declaration         : TASK_PERS identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS("TASK", rapid_ast.PersDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
                
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revG_en_library.pdf
    ###  Constant declarations.    par:2.24
    ###
        
    def p_constant_declaration_1(self, p):
        """ constant_declaration         : CONST identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS(None, rapid_ast.ConstDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);    
        
    def p_constant_declaration_2(self, p):
        """ constant_declaration         : LOCAL_CONST identifier variable_definition SEMI
        """
        p[0] = rapid_ast.DataDefATS("LOCAL", rapid_ast.ConstDeclarationAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Types.    par:2.11
    ###
    
    def p_type_definition_1(self, p):
        """ type_definition         : COMMENT
        """
        p[0] = rapid_ast.CommentAST(p[1], coord=self._coord(p.lineno(1)))
    
    def p_type_definition_2(self, p):
        """ type_definition         : PLACEHOLDER_TDN
        """
        p[0] = rapid_ast.TypeDefAST(None, None, coord=self._coord(p.lineno(1)))
    
    def p_type_definition_3(self, p):
        """ type_definition         : record_definition
                                             | alias_definition
        """
        p[0] = p[1]
    
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Data Types.    par:2.11
    ###
        
    def p_record_definition_1(self, p):
        """ record_definition         : RECORD identifier record_component_list ENDRECORD
        """
        p[0] = rapid_ast.TypeDefAST(None, rapid_ast.RecordDefAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_record_definition_2(self, p):
        """ record_definition         : LOCAL_RECORD identifier record_component_list ENDRECORD
        """
        p[0] = rapid_ast.TypeDefAST("LOCAL",rapid_ast.RecordDefAST(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None)
        
    def p_record_component_list_1(self, p):
        """ record_component_list         : record_component_definition
        """
        p[0] =[ p[1] ]
            
    def p_record_component_list_2(self, p):
        """ record_component_list         : record_component_definition record_component_list
        """
        attriblist = p[2]
        attriblist.insert(0, p[1])
        p[0] = attriblist
        
    def p_record_component_definition(self, p):
        """ record_component_definition         : identifier identifier SEMI
        """
        p[0] = rapid_ast.RecordComponentDefAST(p[1], p[2], coord=None)
        
        
    ###
    ###  IRC5-RAPID Kernel Reference Manual 3HAC16585-1_revB_en_library.pdf
    ###  Alias Types.    par:2.15
    ###
        
    def p_alias_definition_1(self, p):
        """ alias_definition         : ALIAS identifier identifier SEMI
        """
        p[0] = rapid_ast.TypeDefAST(None, rapid_ast.AliasDefATS(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None);
        
    def p_alias_definition_2(self, p):
        """ alias_definition         : LOCAL_ALIAS identifier identifier SEMI
        """
        p[0] = rapid_ast.TypeDefAST("LOCAL", rapid_ast.AliasDefATS(p[2], p[3], coord=self._coord(p.lineno(1))), coord=None)
        

    # END GRAMMAR
        
    def p_error(self, p):
        if p:
            self._parse_error(
                'before: "%s" near charapter %d' % (p.value, self.rapidlex._find_tok_column(p)), 
                self._coord(p.lineno))
            
        else:
            self._parse_error('At end of input', '')


#------------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint
    import time, sys
    
    t1 = time.time()
    parser = RAPIDParser(lex_optimize=False, yacc_debug=True, yacc_optimize=False)
    sys.stdout.write("parse created: "+ str(time.time() - t1))
    
    text = ""
    if len(sys.argv)==2:
        with open(sys.argv[1],'rU') as f:
            text = f.read()
    
    ## set debuglevel to 2 for debugging
    t = parser.parse(text, 'x.rapid', debuglevel=1)
    
    sys.stdout.write("end parse: "+ str(time.time() - t1)+"\n")
    
    t.show(attrnames=True, nodenames=True, showcoord=True)
    
    

