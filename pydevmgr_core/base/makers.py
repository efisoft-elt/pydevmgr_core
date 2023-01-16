from pydevmgr_core.base.node import BaseNode
from pydevmgr_core.base.node_alias import BaseNodeAlias, NodeAlias
from pydevmgr_core.base.rpc import BaseRpc
from .decorators import getter, caller

from pydantic.main import create_model
from typing import  Optional, Union, Type



__all__ = [ 
"nodealias", 
"nodealias_maker", 
"node_maker"
]


def nodealias(*nodes, __base__=NodeAlias, **kwargs):
    return getter(__base__.Config(nodes=nodes, **kwargs))

def rpc(*,Base=BaseRpc):
    return caller(Base.Config())
    

def node_maker(name: Optional[str] = None, *, __base__=BaseNode, include_object=False, **kwargs):
    if kwargs:
        if name:
            Name = name.capitalize()
        else:
            Name = "LambdaNode"
            
        kwargs.setdefault( 'type', Name)
        # Config = type(Name+"Config", (__base__.Config,), kwargs)
        Config = create_model(Name+"Config", __base__ = __base__.Config, **kwargs)
        __base__ = type(Name, (__base__,), {'Config':Config})
    node = __base__(name)
    def fget_decorator(func):
        if include_object:
            def fget(*args):
                return func(node, *args)
        else:
            fget = func

        if not name and hasattr(func, "__name__"):
            node.__path__ = func.__name__
            

        node.fget = fget
        return node
    return fget_decorator

def nodealias_maker(*nodes, **kwargs):
    __base__ = kwargs.pop('__base__', NodeAlias)
    include_object = kwargs.pop('include_object', False)
    
    name = kwargs.pop('name', None) 
    if kwargs:
        if name:
            Name = name.capitalize()
        else:
            Name = "LambdaNodeAlias"
        
        kwargs.setdefault( 'type', Name)
        # Config = type(Name+"Config", (__base__.Config,), kwargs)
        
        Config = create_model(Name+"Config", __base__ = __base__.Config, **kwargs)
        __base__ = type(Name, (__base__,), {'Config':Config})
    node = __base__(name, nodes=nodes) 
    def fget_decorator(func):
        if include_object:
            def fget(*args):
                return func(node, *args)
        else:
            fget = func 
            
        if not name and hasattr(func, "__name__"):
            node.__path__ = func.__name__

        node.fget = fget
        return node
    return fget_decorator

