from enum import Enum
from typing import Any, List, Optional, Tuple, Type
import weakref

from pydantic import BaseModel, Extra, validator

from pydevmgr_core.base.io import load_config

from .engine import BaseEngine 
from .model_var import StaticVar, NodeVar
from systemy import BaseSystem, BaseFactory, SystemDict, SystemList
from systemy import get_factory_class, find_factories

  

class __Decorator__: #  place holder for decorator base class (see base.decorators) 
    pass

def kjoin(*args) -> str:
    """ join key elements """
    return ".".join(a for a in args if a)

def ksplit(key: str) -> Tuple[str,str]:
    """ ksplit(key) ->  prefix, name
    
    >>> ksplit('a.b.c')
    ('a.b', 'c')
    """
    s, _, p = key[::-1].partition(".")
    return p[::-1], s[::-1]

_key_counter = {}
def new_key(cls):
    """ Build a new object key for a class """
    k = cls.__name__ 
    c = _key_counter.setdefault(k,0)
    c += 1
    _key_counter[k] = c
    return f'{k}{c:03d}'


class BaseData(BaseModel):
    # place holder for Data class 
    key: StaticVar[str] = ""

class BaseConfig(BaseSystem.Config):
    """ Configuration for pydevmgr objects """
    class Config:
        validate_assignment = True

    def build(self, parent=None, name=None):
        Object = self.get_system_class()
        if parent:
            return Object.new( parent, name, self)
        key = self._make_new_path(parent, name)
        return Object(key, __config__=self)
    
    @classmethod
    def from_cfgfile(cls, path):
        cfg = load_config(path)
        return cls.parse_obj(cfg)


class BaseObject(BaseSystem):
    """ Pydevmgr object """
    Engine = BaseEngine
    Config = BaseConfig 
    
    _engine = None
    def __init__(self, 
          key: Optional[str] = None,  
          config: Optional[BaseSystem.Config] = None, 
          com: Optional[Any] = None,*, 
          __config__: Optional[BaseSystem.Config] = None,
          __path__: Optional[str]= None, 
          **kwargs 
    ) -> None:
        # keep config for legacy and compatibility  
        if config and __config__:
            raise ValueError("Conflict between config and __config__ argument")
        __config__ = config or __config__

        if key is None:
            key = __path__
        if key is None:
            key = new_key(self.__class__)
        super().__init__( __path__=key, __config__ = __config__, **kwargs)
        self._engine = self.new_engine(com, self.__config__) 
    

    @classmethod
    def new(cls, parent, name, config):
        """ create a new object within a parent pydevmgr object """
        return cls( key=config._make_new_path(parent, name), 
                    com= getattr( parent, "engine", None), # getattr needed is parent is a systemy object  
                    __config__=config
                )

    @classmethod
    def new_engine(cls, com: Any, config: Config)-> Engine:
        """ Create a new engine from a com object and object config """
        return cls.Engine.new(com, config)
        
    @property
    def key(self) -> str:
        return self.__path__

    @property
    def name(self) -> str:
        return ksplit(self.key)[1]    

    @property
    def config(self)-> Config:
        """  config """
        return self.__config__

    @property
    def engine(self)-> Engine:
        """  engine  """
        return self._engine

class ObjectDict(SystemDict):
    """ Dictionary of pydevmgr objects """
    def __setitem__(self, key, system):
        if not isinstance(system, (BaseObject, ObjectDict, ObjectList)):
            raise KeyError(f"item {key} is not a valid item ")
        super().__setitem__(key, system)    

class ObjectList(SystemList):
    """ List of pydevmgr objects """
    def __setitem__(self, index, system):
        if not isinstance(system, (BaseObject, ObjectDict, ObjectList)):
            raise KeyError(f"item {index} is not a valid item ")
        super().__setitem__(index, system)    
  

class ParentWeakRef:
    def get_parent(self):
        return None

    @classmethod
    def new(cls, parent, name, config):
        obj = super().new(parent, name, config)
        obj.get_parent = weakref.ref(parent)
        return obj



