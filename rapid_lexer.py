#-----------------------------------------------------------------
# pyRAPIDparser: rapid_lexer.py
#
# RAPIDLexer class: lexer for the RAPID language
#
#-----------------------------------------------------------------

import re
import sys

import ply.lex
from ply.lex import TOKEN


class RAPIDLexer(object):
    """ A lexer for the RAPID language. After building it, set the
        input text with input(), and call token() to get new 
        tokens.
        
        The public attribute filename can be set to an initial
        filaneme, but the lexer will update it upon #line 
        directives.
    """
    def __init__(self, error_func):
        """ Create a new Lexer.
        
            error_func:
                An error function. Will be called with an error
                message, line and column as arguments, in case of 
                an error during lexing.
                
        """
        self.error_func = error_func
        self.filename = ''

    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be
            called after the lexer object is created. 
            
            This method exists separately, because the PLY
            manual warns against calling lex.lex inside
            __init__
        """
        self.lexer = ply.lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)
    
    def token(self):
        g = self.lexer.token()
        return g

    ######################--   PRIVATE   --######################
    
    ##
    ## Internal auxiliary methods
    ##
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)
    
    def _find_tok_column(self, token):
        i = token.lexpos
        while i > 0:
            if self.lexer.lexdata[i] == '\n': break
            i -= 1
        return (token.lexpos - i) + 1
    
    def _make_tok_location(self, token):
        return (token.lineno, self._find_tok_column(token))
    
    ##
    ## Reserved keywords
    ##
    keywords = (
        'ALIAS',
        'CASE',
        'DEFAULT',
        'ELSE',
        'ENDFUNC',
        'ENDPROC',
        'ENDTRAP',
        'EXIT',
        'FROM',
        'IF',
        'MOD',
        'NOT',
        'PERS',
        'READONLY',
        'RETURN',
        'TEST',
        'TRAP',
        'VAR',
        'WITH',
        'AND',
        'CONNECT',
        'DIV',
        'ELSEIF',
        'ENDIF',
        'ENDRECORD',
        'ENDWHILE',
        'FALSE',
        'FUNC',
        'INOUT',
        'MODULE',
        'NOVIEW',
        'PROC',
        'RECORD',
        'STEP',
        'THEN',
        'TRUE',
        'VIEWONLY',
        'XOR',
        'BACKWARD',
        'CONST',
        'DO',
        'ENDFOR',
        'ENDMODULE',
        'ENDTEST',
        'ERROR',
        'FOR',
        'GOTO',
        'NOSTEPIN',
        'OR',
        'RAISE',
        'RETRY',
        'SYSMODULE',
        'TO',
        'TRYNEXT',
        'WHILE',
        'UNDO', #NOT IN DOCUMENTATION
        'switch',#NOT IN DOCUMENTATION
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword] = keyword

    ##
    ## All the tokens recognized by the lexer
    ##
    tokens = keywords + (
        # Identifiers
        'ID', 
        
        # constants 
        'INT_CONST', 
        'INT_CONST_DEC', 
        'INT_CONST_OCT',        
        'INT_CONST_HEX', 
        'INT_CONST_BIN',         
        'FLOAT_CONST', 
        
        # String literals
        'STRING_LITERAL',

        # Operators 
        'COMMENT',
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
        
        #function argument
        'PIPE', 'CONSLASH', 'CONDOP',
        
        # Assignment
        'EQUALS',
        
        # Delimeters 
        'LPAREN', 'RPAREN',         # ( )
        'LBRACKET', 'RBRACKET',     # [ ]
        'LBRACE', 'RBRACE',         # { } 
        'COMMA', 'PERIOD',          # , .
        'SEMI', 'COLON',            # ; :
        'PERCENT',                  # %
        
        #PLACEHOLDER
        'PLACEHOLDER_TDN',
        'PLACEHOLDER_DDN',
        'PLACEHOLDER_RDN',
        'PLACEHOLDER_PAR',
        'PLACEHOLDER_ALT',
        'PLACEHOLDER_DIM',
        'PLACEHOLDER_SMT',
        'PLACEHOLDER_VAR',
        'PLACEHOLDER_EIT',
        'PLACEHOLDER_CSE',
        'PLACEHOLDER_EXP',
        'PLACEHOLDER_ARG',
        'PLACEHOLDER_ID',
        
        #LOCAL
        'LOCAL_PROC',
        'LOCAL_FUNC',
        'LOCAL_TRAP',
        
        'LOCAL_VAR',
        'LOCAL_CONST',
        'LOCAL_PERS',
        
        'LOCAL_RECORD',
        'LOCAL_ALIAS',
        
        #TASK
        'TASK_VAR',
        'TASK_PERS',
  
    )
    
    local_proc = r'LOCAL[\t\ ]+PROC'
    local_func = r'LOCAL[\t\ ]+FUNC'
    local_trap = r'LOCAL[\t\ ]+TRAP'
    
    @TOKEN(local_proc)
    def t_LOCAL_PROC(self, t):
        t.value = "LOCAL PROC"
        return t
        
    @TOKEN(local_func)
    def t_LOCAL_FUNC(self, t):
        t.value = "LOCAL FUNC"
        return t
    
    @TOKEN(local_trap)
    def t_LOCAL_TRAP(self, t):
        t.value = "LOCAL TRAP"
        return t
        
    local_var = r'LOCAL[\t\ ]+VAR'
    local_const = r'LOCAL[\t\ ]+CONST'
    local_pers = r'LOCAL[\t\ ]+PERS'
    
    #task type is not documented
    task_var = r'TASK[\t\ ]+VAR'
    task_pers = r'TASK[\t\ ]+PERS'
    
    @TOKEN(local_var)
    def t_LOCAL_VAR(self, t):
        t.value = "LOCAL VAR"
        return t
        
    @TOKEN(local_const)
    def t_LOCAL_CONST(self, t):
        t.value = "LOCAL CONST"
        return t
    
    @TOKEN(local_pers)
    def t_LOCAL_PERS(self, t):
        t.value = "LOCAL PERS"
        return t
        
    @TOKEN(task_var)
    def t_TASK_VAR(self, t):
        t.value = "TASK VAR"
        return t
    
    @TOKEN(task_pers)
    def t_TASK_PERS(self, t):
        t.value = "TASK PERS"
        return t
        
    local_record = r'LOCAL[\t\ ]+RECORD'
    local_alias = r'LOCAL[\t\ ]+ALIAS'
    
    @TOKEN(local_record)
    def t_LOCAL_RECORD(self, t):
        t.value = "LOCAL RECORD"
        return t
        
    @TOKEN(local_alias)
    def t_LOCAL_ALIAS(self, t):
        t.value = "LOCAL ALIAS"
        return t
    
    t_PLACEHOLDER_TDN=r'<TDN>'# rapresentation of data type
    t_PLACEHOLDER_DDN=r'<DDN>' # rapresentation of data declaration
    t_PLACEHOLDER_RDN=r'<RDN>' # rapresentation of routine declaration
    t_PLACEHOLDER_PAR=r'<PAR>' # parameter declaration
    t_PLACEHOLDER_ALT=r'<ALT>' # alternative parameter declaration
    t_PLACEHOLDER_DIM=r'<DIM>' # array dimension
    t_PLACEHOLDER_SMT=r'<SMT>' # statement
    t_PLACEHOLDER_VAR=r'<VAR>' # data object
    t_PLACEHOLDER_EIT=r'<EIT>' # else if cause of if statement
    t_PLACEHOLDER_CSE=r'<CSE>' # case clause of test statement
    t_PLACEHOLDER_EXP=r'<EXP>' # expression
    t_PLACEHOLDER_ARG=r'<ARG>' # procedure call argument
    t_PLACEHOLDER_ID=r'<ID>'   # identifier

    ##
    ## Regexes for use in tokens
    ##
    ##

    # valid RAPID identifiers (K&R2: A.2.3)
    identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'

    # integer constants 
    int_constant = '[0-9]+'
    decimal_constant = '0[dD][0-9]+'
    bin_constant = '0[bB][0-1]+'
    hex_constant = '0[xX][0-9a-fA-F]+'
    
    # character constants (K&R2: A.2.5.2)
    # Note: a-zA-Z and '.-~^_!=&;,' are allowed as escape chars to support #line
    # directives with Windows paths as filenames (..\..\dir\file)
    #
    simple_escape = r"""([a-zA-Z._~!=&\^\-\\?'"])"""
    hex_escape = r"""(x[0-9a-fA-F]+)"""
    bad_escape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-7])"""

    escape_sequence = r"""(\\("""+simple_escape+'|'+ hex_escape + '))'
    cconst_char = r"""([^'\\\n]|"""+escape_sequence+')'    
    char_const = "'"+cconst_char+"'"
    unmatched_quote = "('"+cconst_char+"*\\n)|('"+cconst_char+"*$)"
    bad_char_const = r"""('"""+cconst_char+"""[^'\n]+')|('')|('"""+bad_escape+r"""[^'\n]*')"""

    # string literals (K&R2: A.2.6)
    string_char = r"""([^"\\\n]|"""+escape_sequence+')'    
    string_literal = '"'+string_char+'*"'
    bad_string_literal = '"'+string_char+'*'+bad_escape+string_char+'*"'

    # floating constants (K&R2: A.2.5.3)
    exponent_part = r"""([eE][-+]?[0-9]+)"""
    fractional_constant = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
    floating_constant = '(((('+fractional_constant+')'+exponent_part+'?)|([0-9]+'+exponent_part+'))[FfLl]?)'
    
    comment       = r'!.*(\n|\D)'

    
    ##
    ## Rules for the normal state
    ##
    t_ignore = ' \t'

    # Newlines
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        
    #def t_SKEEP(self, t):
    #    r'\r+'
    #    return None

    # Operators
    t_PLUS              = r'\+'
    t_MINUS             = r'-'
    t_TIMES             = r'\*'
    t_DIVIDE            = r'/'
    
    
    t_LT                = r'<'
    t_GT                = r'>'
    t_LE                = r'<='
    t_GE                = r'>='
    t_EQ                = r'='
    t_NE                = r'<>'

    # Assignment operators
    t_EQUALS            = r':='
    
    # |
    t_PIPE         = r'\|'
    # \
    t_CONSLASH         = r'\\'
    # ?
    t_CONDOP            = r'\?'

    # Delimeters
    t_LPAREN            = r'\('
    t_RPAREN            = r'\)'
    t_LBRACKET          = r'\['
    t_RBRACKET          = r'\]'
    t_LBRACE            = r'\{'
    t_RBRACE            = r'\}'
    t_COMMA             = r','
    t_PERIOD            = r'\.'
    t_SEMI              = r';'
    t_COLON             = r':'
    t_PERCENT             = r'%'   

    @TOKEN(string_literal)
    def t_STRING_LITERAL(self, t):
        t.value = t.value[1:-1]
        return t
    
    @TOKEN(comment)
    def t_COMMENT(self, t):
        t.lexer.lineno += t.value.count("\n")
        t.value = t.value[1:].replace('\n','').replace('\D','')
        return t
        #return None
    
    # The following floating and integer constants are defined as 
    # functions to impose a strict order (otherwise, decimal
    # is placed before the others because its regex is longer,
    # and this is bad)
    #
    @TOKEN(floating_constant)
    def t_FLOAT_CONST(self, t):
        t.value = float(t.value)
        return t

    @TOKEN(hex_constant)
    def t_INT_CONST_HEX(self, t):
        t.value = int(t.value, 16)
        return t
        
    @TOKEN(bin_constant)
    def t_BIN_CONST(self, t):
        t.value = int(t.value, 2)
        return t
        
    @TOKEN(int_constant)
    def t_INT_CONST(self, t):
        t.value = int(t.value, 10)
        return t

    @TOKEN(decimal_constant)
    def t_INT_CONST_DEC(self, t):
        t.value = int(t.value, 10)
        return t

    # Must come before bad_char_const, to prevent it from 
    # catching valid char constants as invalid
    # 
            
    @TOKEN(unmatched_quote)
    def t_UNMATCHED_QUOTE(self, t):
        msg = "Unmatched '"
        self._error(msg, t)

    @TOKEN(bad_char_const)
    def t_BAD_CHAR_CONST(self, t):
        msg = "Invalid char constant %s" % t.value
        self._error(msg, t)
    
    # unmatched string literals are caught by the preprocessor
    
    @TOKEN(bad_string_literal)
    def t_BAD_STRING_LITERAL(self, t):
        msg = "String contains invalid escape code" 
        self._error(msg, t)

    @TOKEN(identifier)
    def t_ID(self, t):
        t.type = self.keyword_map.get(t.value, "ID")            
        return t
    
    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)


if __name__ == "__main__":
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
    
    def errfoo(msg, a, b):
        sys.stdout.write(msg + "\n")
        sys.exit()
    
    
    rapidlex = RAPIDLexer(errfoo)
    #module=None, debug=0, optimize=0, lextab='lextab', reflags=0, nowarn=0, outputdir='', debuglog=None, errorlog=None
    rapidlex.build(debug=1)
    rapidlex.input(text)
    
    while 1:
        tok = rapidlex.token()
        if not tok: break
            
        #~ print type(tok)
        print ("token: %s -- type: %s    (line:%d, filename:%s, pos:%d)" % (tok.value, tok.type, tok.lineno, rapidlex.filename, tok.lexpos) )
        
        

