from enum import Enum
from typing import Union, List, Optional, Type, Callable

from systemy.system import BaseFactory

from pydevmgr_core.base.io import add_factory_constructor
from systemy import register_factory, get_factory_class, get_system_class

from pydevmgr_core.base.device import BaseDevice
from pydevmgr_core.base.node import BaseNode 
from pydevmgr_core.base.interface import BaseInterface
from pydevmgr_core.base.manager import BaseManager
from pydevmgr_core.base.rpc import BaseRpc
from valueparser.engine import  Parser

class KINDS(str, Enum):
    PARSER = "Parser"
    NODE = "Node"
    RPC = "Rpc"
    DEVICE = "Device"
    INTERFACE = "Interface"
    MANAGER = "Manager"

default_factory_loockup = {}
def record_default_factory(Factory):
    try:
        kind_field = Factory.__fields__['kind']    
    except (KeyError, AttributeError):
        raise ValueError("Factory is missing 'kind' attribute or is not a BaseModel")
    else:
        kind = kind_field.default  
    
    if kind in default_factory_loockup:
        raise ValueError(f"Default Factory for kind {kind} already recorded")
    default_factory_loockup[kind] = Factory
    return Factory

def get_default_factory(kind):
    try:
        return default_factory_loockup[kind]
    except KeyError:
        raise ValueError( f"Unknow default Factory for kind {kind}")
    

factory_kind_loockup = {  }
factory_loockup = { }

def record_factory(name, __cls__=None, *, kind=None, yaml_tag=None):
    """ record a new fatory 
    
    Usage
    -----

        record_factory( name: str, Factory: BaseFactory)

        or 

        @record_factory(name: str)
        class Factory(BaseFactory):
            ...
    """

    def factory_recorder(cls):
        _record_factory_class(name, cls, kind, yaml_tag)
        return cls 

    if __cls__:
        factory_recorder(__cls__)
        return None
    return factory_recorder


def _record_factory_class(name, cls, kind, yaml_tag):
 
    if not hasattr(cls, "build"):
        raise ValueError("Factory must have a build method")


    if kind is None:
        try:
            kind_field = cls.__fields__['kind']    
        except (KeyError, AttributeError):
            raise ValueError("Cannot figure out output kind of the factory class {cls}")
        else:
            kind = kind_field.default  
        
    factory_kind_loockup.setdefault( name, set() ).add(kind)
    factory_loockup.setdefault( kind, {})[name] = cls    
    
    if yaml_tag:
        add_factory_constructor(yaml_tag, cls)         

def get_factory(arg1, __arg2__=None):
    if __arg2__ is None:
        left, _, right = arg1.partition(":")
        if right:
            kind, name = left, right 
        else:
            kind, name = None, arg1
              
    else:
        kind, name = arg1, __arg2__ 
    
    if kind:
        try:
            return factory_loockup[kind][name]
        except KeyError:
            raise ValueError(f"Unknown Factory of name {name} and kind {kind}")
    else:
        try:
            kinds = factory_kind_loockup[name]
        except KeyError:
            raise ValueError(f"Unknown Factory of name {name}") 
        
        if len(kinds)>1:
            check_list = ", ".join( k+":"+name for k in kinds)
            raise ValueError(f"Embigous Factory name {name}, try one of: {check_list}") 
        kind, = kinds
        
        try:
            return factory_loockup[kind][name]
        except KeyError:
            raise ValueError(f"Bug!!")




object_loockup = {}
def get_class(kind: KINDS, type_: str, default=None) -> Type:
    return get_system_class(type_, kind=kind) 


def _get_string_kind(cls):
    if issubclass(cls, BaseNode):
        return KINDS.NODE
    if issubclass(cls, BaseRpc):
        return KINDS.RPC
    if issubclass(cls, BaseInterface):
        return KINDS.INTERFACE
    if issubclass(cls, BaseDevice):
        return KINDS.DEVICE
    if issubclass(cls, BaseManager):
        return KINDS.MANAGER
    if issubclass(cls, (Parser)):
        return KINDS.PARSER
    return None

def register(
        name_or_cls : Optional[Union[Type,str]] = None, 
         _cls_: Optional[Type] =None, *, 
         namespace: Optional[str] = None,
         kind: Optional[Union[KINDS,str]] =None, 
         yaml_tag: Optional[str] = None, 
     ) -> Callable:
    """ record a new class by its kind and type 
    
    This can be used as decorator or function 
    """
    if isinstance(name_or_cls, type):
        if _cls_ is not None:
            raise ValueError("invalid pair of argument for register")
        name, _cls_ = None, name_or_cls 
    else:
        name, _cls_ = name_or_cls, _cls_ 
        
    if _cls_ is None:
        def obj_decorator(cls) -> Type:
            return register(name, cls, kind=kind, namespace=namespace, yaml_tag=yaml_tag)
        return obj_decorator
    else:
        cls = _cls_

    if not kind:
        kind = _get_string_kind(cls)
    
    if name:
        return register_factory( name, cls, kind=kind, namespace=namespace)
    else:
        return register_factory( cls, kind=kind, namespace=namespace)

record_class = register

 
