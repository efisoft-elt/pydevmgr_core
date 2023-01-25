from numpy.lib.function_base import insert
from pydantic import BaseModel 
from systemy import BaseSystem
import inspect
from typing import Union, Optional, Type, Tuple, Any
VType = Optional[Union[Type, Tuple[Type,Any]]] 


def _vtype_type(vtype):
    """ return a value type from a vtype as defined in BaseNode.Config 

    vtype can be a type or a (type,default) or None 
    If no type is found None is returned 
    """
    if isinstance( vtype, tuple):
        vtype, _ = vtype 
    return vtype 

def _vtype_default(vtype):
    """ return the default value from vtype as defined in BaseNode.Config 
    
    vtype can be a Type or a (Type,default) or None 
    if a tuple is defined return default otherwhise return Type() (without arguments)
    """
    if isinstance( vtype, tuple):
        _, default = vtype 
        return default
    if vtype is None:
        return 
    if not hasattr( vtype, "__call__"):
        return None
    return vtype()

def find_vtype( obj: Union[BaseSystem, Type[BaseSystem], BaseSystem.Config, Type[BaseSystem.Config]]) -> Type:
    if isinstance( obj, type):
        if issubclass( obj, BaseSystem):
            obj = obj.Config 
        if not issubclass( obj, BaseModel):
            raise ValueError( "expecting a BseNode instance a config or a BaseSystem class")
        vtype_field = obj.__fields__['vtype']
        print(vtype_field)
        return vtype_field.get_default()
    return obj.vtype

def nodetype( obj: Union[BaseSystem, Type[BaseSystem], BaseSystem.Config, Type[BaseSystem.Config]]) -> Type:
    return _vtype_type( find_vtype(obj) )

def nodedefault( obj: Union[BaseSystem, Type[BaseSystem], BaseSystem.Config, Type[BaseSystem.Config]]) -> Any:
    return _vtype_default( find_vtype(obj) )



def guess_vtype_from_signature(func):
    annotation = inspect.signature(func).return_annotation
    if annotation is inspect._empty:
        return None 
    if not isinstance( annotation, type):
        return None
    return annotation
