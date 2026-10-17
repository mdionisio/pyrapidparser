from threading import RLock, Lock
from typing import Any, TypeVar

_T = TypeVar("_T", bound="Singleton")


class Singleton(object):
    """
    the class that heredit from this class will be e singletone and the
    __global_init__ will be the init of the singleton
    """

    _lock: Any = Lock()

    def __new__(cls: "type[_T]", *p: Any, **k: Any) -> _T:
        with Singleton._lock:
            if not "_the_instance" in cls.__dict__:
                instance = object.__new__(cls)
                instance._lock = RLock()
                instance.__global_init__(*p, **k)
                setattr(cls, "_the_instance", instance)
        instance = cls.__dict__["_the_instance"]
        assert isinstance(instance, cls)
        return instance

    def __global_init__(self, *p: Any, **k: Any) -> None:
        pass
