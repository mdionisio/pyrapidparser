from threading import RLock, Lock

class Singleton(object):
    """
    the class that heredit from this class will be e singletone and the
    __global_init__ will be the init of the singleton
    """
    
    _lock = Lock()
    def __new__(cls, *p, **k):
        with Singleton._lock:
            if not '_the_instance' in cls.__dict__:
                cls._the_instance = object.__new__(cls)
                cls._the_instance._lock = RLock()
                cls._the_instance.__global_init__(*p, **k)
        return cls._the_instance

