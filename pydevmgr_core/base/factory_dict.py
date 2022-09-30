from pydantic import BaseModel
from pydevmgr_core.base.class_recorder import  get_class, get_default_factory, get_factory

from pydevmgr_core.base.factory_object import ObjectFactory
from .base import ObjectDict, BaseFactory
from .io import add_multi_constructor
import yaml 

from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import Dict, TypeVar, Generic
import copy
from _collections_abc import Mapping
DictVar = TypeVar('DictVar')

class _marker:
    pass

class FactoryDict(BaseFactory, Generic[DictVar]):
    """ A Dictionary of Factory object 

    This is used for instance when configuring a dynamical dictionary of pydevmgr objects 
    
    FactoryDict can be used also as a typing object 

    Args:
        d (optional): A dictionary of key/factory object. A copy (not a deep copy!) is made at init 
        Factory (optional): The factory class to parse-in all items

    Examples:

    ::
        
        from pydevmgr_core import BaseDevice, BaseNode 

        class MyNode(BaseNode):
            ...

        class Mydevice(BaseDevice):
            class Config(BaseDevice.Config):
                nodes: FactoryDict[MyNode.Config] = FactoryDict()
        
        d = Mydevice(nodes = { 'n1':{}, 'n2':{} } )
        assert isinstance( d.nodes['n1'], MyNode)
        
        
        One can put a FactoryDict inside an pydevmgr object (not user configurable)

        class MyDevice(BaseDevice):
            nodes = FactoryDict( { 'n1':{}, 'n2':{} }, MyNode.Config )
        
        d = MyDevices()
        assert isinstance( d.nodes['n1'], MyNode)
    


    """
    __root__: Dict = {}
    
    __Factory__ = None
    
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate
    
    @classmethod
    def validate(cls, v, field: ModelField):
        if not field.sub_fields:
            return FactoryDict(v)
        if len(field.sub_fields)!=1:
            raise ValidationError(['to many field FactoryDict accept only one argument'], cls)

        v_field = field.sub_fields[0]
        Factory = v_field.type_

        if not issubclass(Factory, BaseFactory):
            raise ValidationError([f'expecting a field has Factory got a {type(Factory)}'], cls)
        return FactoryDict(v, Factory) 
   
    def __init__(self, __root__=None, Factory=None):
        if __root__ is not None:
            if isinstance(__root__, FactoryDict):
               __root__ = __root__.__root__.copy()
            else:
                __root__ = {k:self.__cast_item(e, Factory) for k,e in __root__.items()}
        else:
            __root__ = {}
        super().__init__(__root__=__root__)

        if Factory is not None:
            self.__dict__['__Factory__'] = Factory
    
    def build( self, parent = None, name=None):
        if name:
            return ObjectDict( {k:f.build(parent, f'{name}[{k}]' ) for k,f in self.items() } )
        else:
            return ObjectDict( {k:f.build(parent) for k,f in self.items()} )
    
  
    @property
    def Factory(self):
        return self.__Factory__
    
    @classmethod
    def __cast_item(cls, element, Factory):
        Factory = Factory or cls.__Factory__
        
        if Factory:
            return Factory.parse_obj(element)
        else:
            try:
                element.build
            except AttributeError:
                raise ValueError("Item must be a Factory: must have a `build` method")
            return element
    
    def pop(self, key, default=_marker):
        '''D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
          If key is not found, d is returned if given, otherwise KeyError is raised.
        '''
        try:
            value = self[key]
        except KeyError:
            if default is _marker:
                raise
            return default
        else:
            del self[key]
            return value
    
    def clear(self):
        'D.clear() -> None.  Remove all items from D.'
        try:
            while True:
                self.popitem()
        except KeyError:
            pass
    

    def update(*args, **kwds):
        ''' D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
            If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
            If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
            In either case, this is followed by: for k, v in F.items(): D[k] = v
        '''
        if not args:
            raise TypeError("descriptor 'update' of 'MutableMapping' object "
                            "needs an argument")
        self, *args = args
        if len(args) > 1:
            raise TypeError('update expected at most 1 arguments, got %d' %
                            len(args))
        if args:
            other = args[0]
            if isinstance(other, Mapping):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, "keys"):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwds.items():
            self[key] = value

    def keys(self):
        "D.keys() -> a set-like object providing a view on D's keys"
        return self.__root__.keys()
    def items(self):
        "D.items() -> a set-like object providing a view on D's items"
        return self.__root__.items()
    def values(self):
        "D.values() -> an object providing a view on D's values"
        return self.__root__.values()

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    def setdefault(self, key, default=None):
        'D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D'
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default
    


    def __len__(self): return len(self.__root__)
    def __getitem__(self, key):
        if key in self.__root__:
            return self.__root__[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)
    def __setitem__(self, key, item): self.__root__[key] = self.__cast_item(item, self.Factory)
    def __delitem__(self, key): del self.__root__[key]
    def __iter__(self):
        return iter(self.__root__)

    # Modify __contains__ to work correctly when __missing__ is present
    def __contains__(self, key):
        return key in self.__root__

    # Now, add the methods in dicts but not in MutableMapping
    def __repr__(self): return repr(self.__root__)
    def copy(self, deep: bool = False):
        copy_func = copy.deepcopy if deep else copy.copy
        return self.__class__( copy_func(self.__root__), self.Factory)   
    
    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d



def _get_factory_dict_constructor(tag_suffix):
    if not tag_suffix:
        Factory = ObjectFactory
    else:
        Factory = get_factory(tag_suffix) 
    return Factory    

        


def _factory_dict_constructor(loader, tag_suffix, node):
    if isinstance(node, yaml.MappingNode):
        d = loader.construct_mapping(node, deep=True)
        Factory = _get_factory_dict_constructor(tag_suffix)
        return FactoryDict( d, Factory)
    else:
        raise ValueError(f"Expecting a mapping for !DictFactory tag")
        
add_multi_constructor( "!FactoryDict:", _factory_dict_constructor)


