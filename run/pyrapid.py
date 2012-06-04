
from copy import deepcopy
import operator

import Singleton

class GlobalVariable(Singleton.Singleton):
    def __global_init__(self):
        self.global_symbol = {}

class rapid_array :
    def __init__(self, size=[], elem_type=None, val=None):
        if len(size)==0:
            if not (val is None):
                self.Set(val)
            else:
                raise Exception("array not full initialized")
        else:
            self.elem_type = elem_type
            self.size = size
            
            self.val = [ elem_type() for i in range(reduce(operator.mul,self.size)) ]
            
    def toLinear(self, val):
        if isinstance(val, int):
            val = [ val ]
        x = 0
        for i in range(len(self.size),0,-1):
            localsize = self.size[:(i-1)]
            if len(localsize)==0:
                x += val[i-1]
            else:
                x += (reduce(operator.mul,localsize) * val[i-1])
        return (x-1)
        
    def GetElem(self, elem):
        return self.val[ self.toLinear(elem) ]
        
    def SetElem(self, elem, val):
        # add check type
        self.val[ self.toLinear(elem) ] = val
            
    def GetType(self):
        return self.elem_type
        
    def GetSize(self):
        return self.size
        
    def Set(self, val):
        if isinstance(val, rapid_array):
            self.val = deepcopy(val.Get())
            # add type check and compute size
            self.elem_type = val.GetType()
            self.size = val.GetSize()
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val   

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
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
        
class rapid_string :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, string):
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
        
