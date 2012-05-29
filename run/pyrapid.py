
class num :
    def __init__(self, val=None):
        self.val = None
        if not (val is None):
            self.Set(val)
        
    def Set(self, val):
        if isinstance(val, float) or isinstance(val, int):
            self.val = val
        else:
            raise Exception("type unsupported")
        
    def Get(self):
        if self.val is None:
            raise Exception("variable never assigned")
        else:
            return self.val
        
        
