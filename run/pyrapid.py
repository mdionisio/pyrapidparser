from copy import deepcopy
import operator

import Singleton

class Symbol:
    SYM_TYPE_VAR         = 1
    SYM_TYPE_CONST_VAR   = 2
    SYM_TYPE_PERS_VAR    = 3
    SYM_TYPE_FUNCTION    = 4
    SYM_TYPE_PROCEDURE   = 5
    SYM_TYPE_DATATYPE    = 6
    SYM_TYPE_NONE        = 7

    def __init__(self, type, data):
        self.type = type
        self.data = data
        
    def Get(self):
        return (self.type, self.data)
        
    @classmethod
    def CreateNone(cls):
        return cls(cls.SYM_TYPE_NONE, None)
        
    @classmethod
    def CreateDataType(cls, datatype):
        return cls(cls.SYM_TYPE_DATATYPE, datatype)
        
    @staticmethod
    def CreateFunction(parameters, returntype, call=None):
        return SymFunction(parameters, returntype, call)
        
    @staticmethod
    def CreateProcedure(parameters, call=None):
        return SymProcedure(parameters, call)
        
    @staticmethod
    def CreateVar(vartype, varval=None):
        if varval is None:
            return SymVar(type(vartype), vartype)
        else:
            return SymVar(vartype, varval)
        
    @staticmethod
    def CreateConst(vartype, varval=None):
        if varval is None:
            return SymConst(type(vartype), vartype)
        else:
            return SymConst(vartype, varval)
        
    @staticmethod
    def CreatePers(vartype, varval=None):
        if varval is None:
            return SymPers(type(vartype), vartype)
        else:
            return SymPers(vartype, varval)
        
class SymVar(Symbol):
    def __init__(self, vartype, varval):
        Symbol.__init__(self, Symbol.SYM_TYPE_VAR, varval)
        self.vartype = vartype
        
class SymConst(Symbol):
    def __init__(self, vartype, varval):
        Symbol.__init__(self, Symbol.SYM_TYPE_CONST_VAR, varval)
        self.vartype = vartype
        
class SymPers(Symbol):
    def __init__(self, vartype, varval):
        Symbol.__init__(self, Symbol.SYM_TYPE_PERS_VAR, varval)
        self.vartype = vartype
        
class SymFunction(Symbol):
    def __init__(self, parameters, returntype, call):
        Symbol.__init__(self, Symbol.SYM_TYPE_PROCEDURE, call)
        self.parameters = parameters
        self.localsymbol = {}
        self.returntype = returntype
    
    def AddLocalSymbol(self, symbolname, data):
        if self.localsymbol.has_key(symbolname):
            raise Exception("symbol %s already defined"%(symbolname,))
        else:
            self.localsymbol[symbolname] = data
        
class SymProcedure(Symbol):
    def __init__(self, parameters, call):
        Symbol.__init__(self, Symbol.SYM_TYPE_PROCEDURE, call)
        self.parameters = parameters
        self.localsymbol = {}
    
    def AddLocalSymbol(self, symbolname, data):
        if self.localsymbol.has_key(symbolname):
            raise Exception("symbol %s already defined"%(symbolname,))
        else:
            self.localsymbol[symbolname] = data

class Symbols(Singleton.Singleton):
    def __global_init__(self):
        self.reset()
        
    def reset(self):
        self.global_symbol = {}
        self.module_symbol = {}
        self.local_symbol = {}
        self.scope_symbol = []
        self.module_global_symbol = {} # contain for each module the list of global symbol defined
        
    def GetSymbol(self, symbolname, modulename=None, functionname=None):
        try:
            try:
                return self.scope_symbol[-1][2][symbolname]
            except IndexError:
                pass
                #print ("error: there is no scope defined")
            except KeyError:
                pass
            if (functionname is None) and (modulename is None):
                #global
                return self.global_symbol[symbolname]
            elif (modulename is None):
                #module
                try:
                    return self.module_symbol[modulename][symbolname]
                except KeyError:
                    pass
                return self.global_symbol[symbolname]
            else:
                #local
                try:
                    return self.local_symbol[modulename][functionname][symbolname]
                except KeyError:
                    pass
                try:
                    return self.module_symbol[modulename][symbolname]
                except KeyError:
                    pass
                return self.global_symbol[symbolname]
        except KeyError:
            return None
            
    def IsInScope(self, symbolname):
        try:
            return self.scope_symbol[-1][2].has_key(symbolname)
        except:
            return False
            
    def UnLoadModule(self, modulename):
        if self.module_global_symbol.has_key(modulename):
            for i in self.module_global_symbol[modulename]:
                self.global_symbol.pop(i)
            self.module_global_symbol.pop(modulename)
            
        
    def AddGlobalSym(self, symbolname, data, modulename=None):
        if self.global_symbol.has_key(symbolname):
            raise Exception("symbol %s already defined"%(symbolname,))
        else:
            self.global_symbol[symbolname] = data
            if not(modulename is None):
                if self.module_global_symbol.has_key(modulename):
                    self.module_global_symbol[modulename].append(symbolname)
                else:
                    self.module_global_symbol[modulename] = [ symbolname ]
        
    def AddModuleSym(self, module, symbolname, data):
        if not self.module_symbol.has_key(module):
            self.module_symbol[module] = {}
        msymbol = self.module_symbol[module]
        if msymbol.has_key(symbolname):    
            raise Exception("symbol %s already defined in module %s"%(symbolname,module))
        else:
            msymbol[symbolname] = data
            
    class Scope():
        def __init__(self, modulename, functionname=None, invalue={}):
            self.modulename = modulename
            self.functionname = functionname
            self.invalue = invalue
            
        def __enter__(self):
            Symbols().PushScope(self.modulename, self.functionname, self.invalue)
            return Symbols()
            
        def __exit__(self, type, value, traceback):
            Symbols().PopScope()
            
    def PushScope(self, modulename, functionname=None, invalue={}):
        self.scope_symbol.append( ( modulename, functionname, invalue ) )
        
    def PopScope(self):
        self.scope_symbol.pop()
        
    def AddScopeSym(self, symbolname, data):
        modulename = self.scope_symbol[-1][0]
        functionname = self.scope_symbol[-1][1]
        symbols = self.scope_symbol[-1][2]
        if symbols.has_key(symbolname):
            raise Exception("symbol %s already defined in the scope"%(symbolname,))
        elif self.local_symbol.has_key(modulename) and self.local_symbol[modulename].has_key(functionname) and self.local_symbol[modulename][functionname].has_key(symbolname):
            raise Exception("symbol %s already defined in the local scope"%(symbolname,))
        else:
            symbols[symbolname] = data
            
        
    def AddLocalSym(self, module, function, symbolname, data):
        if not self.local_symbol.has_key(module):
            self.local_symbol[module] = {}
        msymbol = self.local_symbol[module]
        if not msymbol.has_key(function):
            raise Exception("function/procedure %s never defined in %s"%(function,module))
        lsymbol = msymbol[function]
        lsymbol.AddLocalSymbol(symbolname, data)
        
        
        
class ModuleSymbol(Singleton.Singleton):
    def __global_init__(self):
        self.global_symbol = {}
        
class rapid_struct :
    def __init__(self, names, types):
        self.names = names
        self.types = types
        self.val = [ self.types[i]() for i in range(0, len(self.names)) ]
        
    def GetElem(self, elem):
        if isinstance(elem, int):
            return self.val[ elem ]
        else:
            return self.val[ self.names.index(elem) ]
        
    def SetElem(self, elem, val):
        # add check type
        if isinstance(elem, int):
            self.val[ self.toLinear(elem) ] = val
        else:
            self.val[ self.names.index(elem) ] = val
            
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self
            
    def Set(self, val):
        if isinstance(val, list) and len(val)==len(self.names):
            for i in range(0, len(val)):
                self.val[i].Set( val[i] )
        else:
            raise Exception("has to be implemented val:%s, type:%s (%s)"%(str(val),str(type(val)),str(self.names)))

class rapid_array :
    def __init__(self, size=[], elem_type=None, val=None):
        if len(size)==0:
            if not (val is None):
                self.elem_type = elem_type
                self.Set(val)
            else:
                self.size = None
                self.elem_type = elem_type
        else:
            self.elem_type = elem_type
            self.size = None
            self.SetSize(size, val)
            
            
    def SetSize(self, size, val=None):
        if self.size is None:
            if val is None:
                self.size = size
                self.val = [ self.elem_type() for i in range(reduce(operator.mul,self.size)) ]
            else:
                self.size = size
                val, psize =  rapid_array.unrollarray(val)
                self.val = [ self.elem_type(val[i]) for i in range(reduce(operator.mul,self.size)) ]
        else:
            raise Exception("size already defined")
            
    @staticmethod
    def unrollarray(indata):
        out = []
        psize = [ len(indata) ]
        tmp_psize = None
        for i in indata:
            if isinstance(i, list):
                outt, psizet = rapid_array.unrollarray(i) 
                out += outt 
                if tmp_psize is None:
                    tmp_psize = psizet
                elif tmp_psize != psizet:
                    raise Exception("it is not an array")
            else:
                out.append(i)
        if not (tmp_psize is None):
            psize += tmp_psize
        return (out, psize)
            
    def toLinear(self, val):
        if isinstance(val, int):
            val = [ val ]
            
        x = 0
        for i in range(len(self.size),0,-1):
            localsize = self.size[:(i-1)]
            if len(localsize)==0:
                tmp = val[i-1]
                if isinstance(tmp, int):
                    x += tmp
                else:
                    x += tmp.data.Get()
            else:
                x += (reduce(operator.mul,localsize) * val[i-1])
        return (x-1)
        
    def GetElem(self, elem):
        if isinstance(elem, int):
            ielem = elem;
        elif isinstance(elem, list):
            ielem = elem;
        elif isinstance(elem, tuple):
            ielem = elem;
        else:
            ielem = elem.Get();
        return self.val[ self.toLinear(ielem) ]
        
    def SetElem(self, elem, val):
        # add check type
        if isinstance(elem, int):
            ielem = elem;
        elif isinstance(elem, list):
            ielem = elem;
        elif isinstance(elem, tuple):
            ielem = elem;
        else:
            ielem = elem.Get();
        self.val[ self.toLinear(ielem) ] = val
            
    def GetType(self):
        return self.elem_type
        
    def GetSize(self, DimNo=None):
        if DimNo is None:
            return self.size
        else:
            if isinstance(DimNo, int):
                return self.size[DimNo - 1]
            else:
                return self.size[DimNo.data.Get() - 1]
        
    def Set(self, val):
        if isinstance(val, rapid_array):
            self.val = deepcopy(val.Get())
            # add type check and compute size
            self.elem_type = val.GetType()
            self.size = val.GetSize()
        elif isinstance(val, list):
            val, psize =  rapid_array.unrollarray(val)
            self.size = [ len(val) ]
            self.val = [ self.elem_type(val[i]) for i in range(reduce(operator.mul,self.size)) ]
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val  
            
class rapid_anytype :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        self.val = val
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("anytype", Symbol.CreateDataType(rapid_anytype))

class rapid_num :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, float) or isinstance(val, int):
            self.val = val
        elif isinstance(val, rapid_num):
            self.val = val.val
        else:
            raise Exception("type unsupported val=%s has to be a number"%(str(val)))
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("num", Symbol.CreateDataType(rapid_num))
            
class rapid_byte :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, int):
            self.val = val
        elif isinstance(val, rapid_byte):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("byte", Symbol.CreateDataType(rapid_byte))
            
class rapid_clock :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, tuple):
            self.val = val
        elif isinstance(val, rapid_clock):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("clock", Symbol.CreateDataType(rapid_clock))
            
class rapid_bool :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, bool):
            self.val = val
        elif isinstance(val, rapid_bool):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("bool", Symbol.CreateDataType(rapid_bool))
        
class rapid_string :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, str):
            self.val = val
        elif isinstance(val, rapid_string):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("string", Symbol.CreateDataType(rapid_string))
        
class rapid_Confdata (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["cf1", "cf4", "cf6", "cfx"], [rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_Confdata):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("Confdata", Symbol.CreateDataType(rapid_Confdata))
            
class rapid_dionum :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, int) and ( (val == 1) or (val == 0) ):
            self.val = val
        elif isinstance(val, rapid_dionum):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("dionum", Symbol.CreateDataType(rapid_dionum))

class rapid_errnum :
    __error__ = 0
    def __init__(self, val=None):
        if (val is None):
            rapid_errnum.__error__ += 1
            self.val = rapid_errnum.__error__
        else:
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, int):
            self.val = val
        elif isinstance(val, rapid_errnum):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("errnum", Symbol.CreateDataType(rapid_errnum))
            
Symbols().AddGlobalSym("ERR_ALRDYCNT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CNTNOTVAR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CNV_NOT_ACT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CNV_CONNECT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CNV_DROPPED", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_DEV_MAXTIME", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ARGDUPCND", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ARGNAME", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ARGNOTPER", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ARGNOTVAR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_AXIS_ACT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_AXIS_IND", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_AXIS_MOVING", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_AXIS_PAR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CALLIO_INTER", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_CALLPROC", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_DIVZERO", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_EXCRTYMAX", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_EXECPHR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_FILEACC", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_FILEOPEN", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_FILNOTFND", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_FNCNORET", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_FRAME", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ILLDIM", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ILLQUAT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_ILLRAISE", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_INOMAX", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_IOENABLE", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_IOERROR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_IODISABLE", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_LOADED", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_LOADID_FATAL", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_LOADID_RETRY", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_MAXINTVAL", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_MODULE", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NAME_INVALID", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NEGARG", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NOTARR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NOTEQDIM", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NOTINTVAL", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_NOTPRES", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_OUTOFBND", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_PATH", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_PATHDIST", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_PID_MOVESTOP", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_PID_RAISE_PP", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_RCVDATA", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_REFUNKDAT", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_REFUNKFUN", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_REFUNKPRC", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_REFUNKTRP", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_SC_WRITE", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_SIGSUPSEARCH", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_STEP_PAR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_STRTOOLNG", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_SYM_ACCESS", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_TP_DIBREAK", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_TP_MAXTIME", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_UNIT_PAR", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_UNKINO", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_UNKPROC", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_UNLOAD", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_WAIT_MAXTIME", Symbol.CreateConst(rapid_errnum, rapid_errnum()))
Symbols().AddGlobalSym("ERR_WHLSEARCH", Symbol.CreateConst(rapid_errnum, rapid_errnum()))


class rapid_extjoint (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["eax_a", "eax_b", "eax_c", "eax_d", "eax_e", "eax_f"], [rapid_num, rapid_num, rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_extjoint):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)

Symbols().AddGlobalSym("extjoint", Symbol.CreateDataType(rapid_extjoint))
            
class rapid_intnum :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, int):
            self.val = val
        elif isinstance(val, rapid_intnum):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
            
Symbols().AddGlobalSym("intnum", Symbol.CreateDataType(rapid_intnum))

class rapid_iodev :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, string):
            self.val = val
        elif isinstance(val, rapid_iodev):
            self.val = val.val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val

Symbols().AddGlobalSym("iodev", Symbol.CreateDataType(rapid_iodev))

class rapid_jointtarget (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["robax", "extax"], [rapid_robjoint, rapid_extjoint])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_jointtarget):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("jointtarget", Symbol.CreateDataType(rapid_jointtarget))

class rapid_loaddata (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["mass", "cog", "aom", "ix", "iy", "iz"], [rapid_num, rapid_pos, rapid_orient, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_loaddata):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("loaddata", Symbol.CreateDataType(rapid_loaddata))

#todo define loadsession
#todo define mecunit
#todo defne motsetdata

class rapid_o_jointtarget (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["robax", "extax"], [rapid_robjoint, rapid_extjoint])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_o_jointtarget):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("o_jointtarget", Symbol.CreateDataType(rapid_o_jointtarget))

class rapid_orient (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["q1", "q2", "q3", "q4"], [rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_orient):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("orient", Symbol.CreateDataType(rapid_orient))

class rapid_o_robtarget (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["trans", "rot", "robconf", "extax"], [rapid_pos, rapid_orient, rapid_confdata, rapid_extjoint])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_o_robtarget):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("o_robtarget", Symbol.CreateDataType(rapid_o_robtarget))

class rapid_pos (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["x", "y", "z"], [rapid_num, rapid_num, rapid_num])
        if not(val is None):
            self.Set( val )
           
    def Set(self, val):
        if isinstance(val, rapid_pos):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("pos", Symbol.CreateDataType(rapid_pos))
            
class rapid_pose (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["trans", "rot"], [rapid_pos, rapid_orient])
        if not(val is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_pose):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("pose", Symbol.CreateDataType(rapid_pose))            

class rapid_progdisp (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["pdisp", "eoffs"], [rapid_pose, rapid_extjoints])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_progdisp):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("progdisp", Symbol.CreateDataType(rapid_progdisp))  


class rapid_robjoint (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["rax_1", "rax_2", "rax_3", "rax_4", "rax_5", "rax_6"], [rapid_num, rapid_num, rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_robjoint):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("robjoint", Symbol.CreateDataType(rapid_robjoint))            

class rapid_robtarget (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["trans", "rot", "robconf", "extax"], [rapid_pos, rapid_orient, rapid_confdata, rapid_extjoint])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_robtarget):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("robtarget", Symbol.CreateDataType(rapid_robtarget))

#todo define shapedata
#todo define signalai 
#todo define signalao
#todo define signaldi 
#todo define signaldo
#todo define signalgi
#todo define signalgo

class rapid_speeddata (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["v_tcp", "v_ori", "v_leax", "v_reax"], [rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_speeddata):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("speeddata", Symbol.CreateDataType(rapid_speeddata))

Symbols().AddGlobalSym("v5", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([5, 500, 5000, 1000])))
Symbols().AddGlobalSym("v10", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([10, 500, 5000, 1000])))
Symbols().AddGlobalSym("v20", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([20, 500, 5000, 1000])))
Symbols().AddGlobalSym("v30", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([30, 500, 5000, 1000])))
Symbols().AddGlobalSym("v40", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([40, 500, 5000, 1000])))
Symbols().AddGlobalSym("v60", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([60, 500, 5000, 1000])))
Symbols().AddGlobalSym("v80", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([80, 500, 5000, 1000])))
Symbols().AddGlobalSym("v100", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([100, 500, 5000, 1000])))
Symbols().AddGlobalSym("v150", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([150, 500, 5000, 1000])))
Symbols().AddGlobalSym("v200", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([200, 500, 5000, 1000])))
Symbols().AddGlobalSym("v300", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([300, 500, 5000, 1000])))
Symbols().AddGlobalSym("v400", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([400, 500, 5000, 1000])))
Symbols().AddGlobalSym("v500", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([500, 500, 5000, 1000])))
Symbols().AddGlobalSym("v600", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([600, 500, 5000, 1000])))
Symbols().AddGlobalSym("v800", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([800, 500, 5000, 1000])))
Symbols().AddGlobalSym("v1000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([1000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v1500", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([1500, 500, 5000, 1000])))
Symbols().AddGlobalSym("v2000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([2000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v2500", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([2500, 500, 5000, 1000])))
Symbols().AddGlobalSym("v3000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([3000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v4000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([4000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v5000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([5000, 500, 5000, 1000])))
Symbols().AddGlobalSym("vmax", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([5000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v6000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([6000, 500, 5000, 1000])))
Symbols().AddGlobalSym("v7000", Symbol.CreateConst(rapid_speeddata, rapid_speeddata([7000, 500, 5000, 1000])))

#todo define symnum
#todo define constant
#RUN_UNDEF 
#RUN_CONT_CYCLE 
#RUN_INSTR_FWD 
#RUN_INSTR_BWD 
#RUN_SIM 
#OP_UNDEF 
#OP_AUTO 
#OP_MAN_PROG 
#OP_MAN_TEST 


#define also

#C_MOTSET 
#C_PROGDISP 
#ERRNO 
#INTNO 


#todo define taskid

class rapid_tooldata (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["robhold", "tframe", "tload"], [rapid_bool, rapid_pose, rapid_loaddata])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_tooldata):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("tooldata", Symbol.CreateDataType(rapid_tooldata))

#todo define tpnum

#todo define contant
#TP_PROGRAM 
#TP_LATEST 

#todo define triggdata
#todo define tunetype

#todo define contant
#TUNE_DF 
#TUNE_KP 
#TUNE_KV 
#TUNE_TI 
#TUNE_FRIC_LEV 
#TUNE_FRIC_RAMP 
#SP_MODE1 
#SP_MODE2 

#todo define wobjdata

#todo define wzstationary

#todo define zonedata

class rapid_zonedata (rapid_struct):
    def __init__(self, val=None):
        rapid_struct.__init__(self, ["finep", "pzone_tcp", "pzone_ori", "pzone_eax", "zone_ori", "zone_leax", "zone_reax"], [rapid_bool, rapid_num, rapid_num, rapid_num, rapid_num, rapid_num, rapid_num])
        if not(val  is None):
            self.Set( val )
            
    def Set(self, val):
        if isinstance(val, rapid_zonedata):
            self.val = val.val
        else:
            rapid_struct.Set(self, val)
            
Symbols().AddGlobalSym("zonedata", Symbol.CreateDataType(rapid_zonedata))


Symbols().AddGlobalSym("fine", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([True, 0, 0, 0, 0, 0, 0])))
Symbols().AddGlobalSym("z1", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 1, 1, 1, 0.1, 1, 0.1])))
Symbols().AddGlobalSym("z5", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 5, 8, 8, 0.8, 8, 0.8])))
Symbols().AddGlobalSym("z10", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 10, 15, 15, 1.5, 15, 1.5])))
Symbols().AddGlobalSym("z15", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 15, 23, 23, 2.3, 23, 2.3])))
Symbols().AddGlobalSym("z20", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 20, 30, 30, 3.0, 30, 3.0])))
Symbols().AddGlobalSym("z30", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 30, 45, 45, 4.5, 45, 4.5])))
Symbols().AddGlobalSym("z40", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 40, 60, 60, 6.0, 60, 6.0])))
Symbols().AddGlobalSym("z50", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 50, 75, 75, 7.5, 75, 7.5])))
Symbols().AddGlobalSym("z60", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 60, 90, 90, 9.0, 90, 9.0])))
Symbols().AddGlobalSym("z80", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 80, 120, 120, 12.0, 120, 12.0])))
Symbols().AddGlobalSym("z100", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 100, 150, 150, 12.0, 120, 12.0])))
Symbols().AddGlobalSym("z150", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 150, 225, 225, 23.0, 225, 23.0])))
Symbols().AddGlobalSym("z200", Symbol.CreateConst(rapid_zonedata, rapid_zonedata([False, 200, 300, 300, 30.0, 300, 30.0])))











