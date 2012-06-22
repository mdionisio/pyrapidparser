#-----------------------------------------------------------------
# _ast_gen.py
#
# Generates the AST Node classes from a specification given in 
# a .yaml file
#
# The design of this module was inspired by astgen.py from the
# Python 2.5 code-base.
#
# Copyright (C) 2008-2012, Eli Bendersky
# License: BSD
#-----------------------------------------------------------------
import pprint
from string import Template


class ASTCodeGenerator(object):
    def __init__(self, cfg_filename='_rapid_ast.cfg'):
        """ Initialize the code generator from a configuration
            file.
        """
        self.cfg_filename = cfg_filename
        self.node_cfg = [NodeCfg(name, contents) 
            for (name, contents) in self.parse_cfgfile(cfg_filename)]

    def generate(self, file=None):
        """ Generates the code into file, an open file buffer.
        """
        src = Template(_PROLOGUE_COMMENT).substitute(
            cfg_filename=self.cfg_filename)
        
        src += _PROLOGUE_CODE
        for node_cfg in self.node_cfg:
            src += node_cfg.generate_source() + '\n\n'
        
        file.write(src)

    def parse_cfgfile(self, filename):
        """ Parse the configuration file and yield pairs of
            (name, contents) for each node.
        """
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                colon_i = line.find(':')
                lbracket_i = line.find('[')
                rbracket_i = line.find(']')
                if colon_i < 1 or lbracket_i <= colon_i or rbracket_i <= lbracket_i:
                    raise RuntimeError("Invalid line in %s:\n%s\n" % (filename, line))

                name = line[:colon_i]
                val = line[lbracket_i + 1:rbracket_i]
                vallist = [v.strip() for v in val.split(',')] if val else []
                yield name, vallist


class NodeCfg(object):
    """ Node configuration. 

        name: node name
        contents: a list of contents - attributes and child nodes 
        See comment at the top of the configuration file for details.
    """
    def __init__(self, name, contents):
        self.name = name
        self.all_entries = []
        self.attr = []
        self.child = []
        self.seq_child = []

        for entry in contents:
            if len(entry)>0:
                clean_entry = entry.rstrip('*')
                self.all_entries.append(clean_entry)
                
                if entry.endswith('**'):
                    self.seq_child.append(clean_entry)
                elif entry.endswith('*'):
                    self.child.append(clean_entry)
                else:
                    self.attr.append(entry)

    def generate_source(self):
        src = self._gen_init()
        src += '\n' + self._gen_children()
        src += '\n' + self._gen_attr_names()
        return src
    
    def _gen_init(self):
        src = "class %s(Node):\n" % self.name

        if len(self.all_entries)>0:
            args = ', '.join(self.all_entries)
            arglist = '(self, %s, coord=None)' % args
        else:
            arglist = '(self, coord=None)'
        
        src += "    def __init__%s:\n" % arglist
        
        for name in self.all_entries + ['coord']:
            src += "        self.%s = %s\n" % (name, name)
        
        return src

    def _gen_children(self):
        src = '    def children(self):\n'
        
        if self.all_entries:
            src += '        nodelist = []\n'

            for child in self.child:
                src += (
                    '        if self.%(child)s is not None:' +
                    ' nodelist.append(("%(child)s", self.%(child)s))\n') % (
                        dict(child=child))
                
            for seq_child in self.seq_child:
                src += (
                    '        for i, child in enumerate(self.%(child)s or []):\n'
                    '            nodelist.append(("%(child)s[%%d]" %% (i,), child))\n') % (
                        dict(child=seq_child))
                    
            src += '        return tuple(nodelist)\n'
        else:
            src += '        return ()\n'
            
        return src        

    def _gen_attr_names(self):
        src = "    attr_names = (" + ''.join("%r," % nm for nm in self.attr) + ')' 
        return src


_PROLOGUE_COMMENT = \
r'''#-----------------------------------------------------------------
# ** ATTENTION **
# This code was automatically generated from the file:
# $cfg_filename 
#
# Do not modify it directly. Modify the configuration file and
# run the generator again.
# ** ** *** ** **
#
# pyRAPIDparser: rapid_ast.py
#
# AST Node classes.
#
# Copyright (C) 2008-2012, Eli Bendersky
# License: BSD
#-----------------------------------------------------------------

'''

_PROLOGUE_CODE = r'''
import sys
from ast_gen import UnknownShow, Node, NodeVisitor, NodeCompare

'''


if __name__ == "__main__":
    import sys
    ast_gen = ASTCodeGenerator('_rapid_ast.cfg')
    ast_gen.generate(open('rapid_ast.py', 'w'))

