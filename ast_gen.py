import sys

def UnknownShow(child, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, _my_node_name=None):
    lead = ' ' * offset
    buf.write(' ' * (offset+2))
    if nodenames and _my_node_name is not None:
        buf.write(lead + ' <' + _my_node_name + '>: ')
    else:
        buf.write(lead + ': ')
        
    if child is None:
        buf.write("None")
    elif isinstance(child, str):
        buf.write("string: %s" % child)
    elif isinstance(child, int):
        buf.write("int : %d" % child)
    elif isinstance(child, float):
        buf.write("float: %f" % child)
    elif isinstance(child, bool):
        buf.write("bool: %b" % child)
        
    buf.write('\n')


class Node(object):
    """ Abstract base class for AST nodes.
    """
    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and
            children (recursively) to a buffer.
            
            buf:   
                Open IO buffer into which the Node is printed.
            
            offset: 
                Initial offset (amount of leading spaces) 
            
            attrnames:
                True if you want to see the attribute names in
                name=value pairs. False to only see the values.
                
            nodenames:
                True if you want to see the actual node names 
                within their parents.
            
            showcoord:
                Do you want the coordinates of each Node to be
                displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self,n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if not(self.coord is None):
                buf.write(' (at %s)' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            if ( (child is None) or 
                isinstance(child, str) or 
                isinstance(child, int) or 
                isinstance(child, float) or 
                isinstance(child, bool) ) :
                UnknownShow(child, buf=sys.stdout, offset=(offset+2), attrnames=attrnames, nodenames=nodenames, _my_node_name=child_name)
            else:
                child.show(
                    buf,
                    offset=offset + 2,
                    attrnames=attrnames,
                    nodenames=nodenames,
                    showcoord=showcoord,
                    _my_node_name=child_name)

class NodeVisitor(object):
    """ A base NodeVisitor class for visiting rapid_ast nodes. 
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these 
        methods.
        
        For example:
        
        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []
            
            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the constant nodes 
        encountered below the given node. To use it:
        
        cv = ConstantVisitor()
        cv.visit(node)
        
        Notes:
        
        *   generic_visit() will be called for AST nodes for which 
            no visit_XXX method was defined. 
        *   The children of nodes for which a visit_XXX was 
            defined will not be visited - if you need this, call
            generic_visit() on the node. 
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """
    def pre_visit(self, node, **kwargs):
        """ Visit a node. 
        """
        method = 'pre_visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if not (visitor is None):
            visitor(node, **kwargs)
            
    def post_visit(self, node, **kwargs):
        """ Visit a node. 
        """
        method = 'post_visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if not (visitor is None):
            visitor(node, **kwargs)
            
    def visit(self, node, **kwargs):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, **kwargs)
                
    def generic_visit(self, node, **kwargs):
        """ Called if no explicit visitor function exists for a 
            node. Implements preorder visiting of the node.
        """
        self.pre_visit(node, **kwargs)
        try:
            for c_name, c in node.children():
                self.visit(c, **kwargs)
        finally:
            self.post_visit(node, **kwargs)
            
class NodeCompare(object):
    """ A base NodeCompare class for comparing compare_ast nodes. 
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these 
        methods.
        
        For example:
        
        class ConstantCompare(NodeCompare):
            def __init__(self):
                pass
            
            def compare_Constant(self, node1, node2):
                return (node1 == node2)

        Creates a list of values of all the constant nodes 
        encountered below the given node. To use it:
        
        cv = ConstantCompare()
        cv.compare(node1, node2)
        
        Notes:
        
        *   generic_visit() will be called for AST nodes for which 
            no visit_XXX method was defined. 
        *   The children of nodes for which a visit_XXX was 
            defined will not be visited - if you need this, call
            generic_visit() on the node. 
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """
    
    def generic_compare(self, node1, node2):
        """ Not defince compare function 
        """
        ret = True
        for i in node1.attr_names:
            n1 = eval("node1.%s"%(i,))
            n2 = eval("node2.%s"%(i,))
            ret &= (n1 == n2)
        return ret
    
    def compare(self, node1, node2):
        """ Visit a node. 
        """
        if type(node1)==type(node2):
            method = 'compare_' + node1.__class__.__name__
            compare = getattr(self, method, self.generic_compare)
            return compare(node1, node2)
        return False
                
    def full_compare(self, node1, node2):
        """ Called if no explicit visitor function exists for a 
            node. Implements preorder visiting of the node.
        """
        child1 = node1.children()
        child2 = node2.children()
        
        if self.compare(node1, node2) and (len(child1) == len(child2)):
            ret = True
            for c1, c2 in zip(child1, child2):
                c_name1, c_next1 = c1
                c_name2, c_next2 = c2
                if isinstance(c_next1, list):
                    for c_next1_1, c_next2_2 in zip(c_next1, c_next2):
                        ret &= self.full_compare(c_next1_1, c_next2_2)
                else:
                    ret &= self.full_compare(c_next1, c_next2)
            return ret
        return False

