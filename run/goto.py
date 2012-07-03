import dis
import new

class MissingLabelError(Exception):
    """'goto' without matching 'label'."""
    pass


def goto(fn):
    """
    A function decorator to add the goto command for a function.

    Specify labels like so:

    label .foo
    
    Goto labels like so:

    goto .foo
    """
    labels = {}
    gotos = {}
    reflabel = {}
    globalName = None
    index = 0
    end = len(fn.func_code.co_code)
    i = 0

    # scan through the byte codes to find the labels and gotos
    while i < end:
        op = ord(fn.func_code.co_code[i])
        i += 1
        name = dis.opname[op]

        if op > dis.HAVE_ARGUMENT:
            b1 = ord(fn.func_code.co_code[i])
            b2 = ord(fn.func_code.co_code[i+1])
            num = b2 * 256 + b1
            
            if name == 'LOAD_GLOBAL':
                globalName = fn.func_code.co_names[num]
                index = i - 1
                i += 2
                continue
                
            if name == 'LOAD_ATTR':
                if globalName == 'label':
                    labels[fn.func_code.co_names[num]] = index
                elif globalName == 'goto':
                    gotos[index] = fn.func_code.co_names[num]
                    
            name = None
            i += 2

    # no-op the labels
    ilist = list(fn.func_code.co_code)
    for label,index in labels.items():
        ilist[index:index+7] = [chr(dis.opmap['NOP'])]*7

        
    # change gotos to jumps
    for index,label in gotos.items():
        if label not in labels:
            raise MissingLabelError("Missing label: %s"%label)
        
        ilist[index:index+7] = [chr(dis.opmap['NOP'])]*7
        
        target = labels[label] + 7   # skip NOPs
        ilist[index] = chr(dis.opmap['JUMP_ABSOLUTE'])
        ilist[index + 1] = chr(target & 255)
        ilist[index + 2] = chr(target >> 8)

    # create new function from existing function
    c = fn.func_code
    newcode = new.code(c.co_argcount,
                       c.co_nlocals,
                       c.co_stacksize,
                       c.co_flags,
                       ''.join(ilist),
                       c.co_consts,
                       c.co_names,
                       c.co_varnames,
                       c.co_filename,
                       c.co_name,
                       c.co_firstlineno,
                       c.co_lnotab)
    newfn = new.function(newcode,fn.func_globals)
    return newfn


if __name__ == '__main__':
    
    @goto
    def test3():

        s = 0
        
        goto .myOut1
        
        s = 1
        
        goto .myOut1
        
        s = 2

        label .myOut1
        
        return s
        
    print test3()
    assert(test3() == 0)
    
    @goto
    def test1(n):

        s = 0

        label .myLoop

        if n <= 0:
            return s
        s += n
        n -= 1

        goto .myLoop
        
    print test1(10)
    assert(test1(10) == 55)
        
    @goto
    def test2():

        s = 0
        
        goto .myOut
        
        s = 1

        label .myOut
        
        return s
    
    
    print test2()
    assert(test2() == 0)
    
    
    
