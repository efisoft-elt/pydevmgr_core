from pydantic import BaseModel 
from .base import  BaseFactory, ObjectList
from .io import add_multi_constructor

from .factory_dict import _get_factory_dict_constructor
import yaml 

from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import List, TypeVar, Generic
import copy
ListVar = TypeVar('ListVar')


class FactoryList(BaseFactory, Generic[ListVar]):

    """ A List of Factory object 

    This is used for instance when configuring a dynamical wlist of pydevmgr objects 
    
    Args:
        l (optional): A list of factory object. A copy (not a deep copy!) is made at init 
        Factory (optional): The factory class to parse-in all items

    Examples:

    ::
        
        from pydevmgr_core import BaseDevice, BaseNode 

        class MyNode(BaseNode, some_param= 0):
            ...

        class Mydevice(BaseDevice):
            class Config(BaseDevice.Config):
                nodes: FactoryList[MyNode.Config] = FactoryList()
        
        d = Mydevice(nodes = [{'some_param':1}, {'some_param':2}] )
        assert isinstance( d.nodes[0], MyNode)
        assert d.nodes[0]config.some_param == 1 
        assert d.nodes[1]config.some_param == 2 
    
    """

    __root__: List = []
    
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
            return FactoryList(v)
        if len(field.sub_fields)!=1:
            raise ValidationError(['to many field FactoryList accept only one argument'], cls)

        v_field = field.sub_fields[0]
        Factory = v_field.type_

        if not issubclass(Factory, BaseFactory):
            raise ValidationError([f'expecting a field has Factory got a {type(Factory)}'], cls)
        return FactoryList(v, Factory) 
    
    def build( self, parent=None, name=None):
        if name:
            return ObjectList( [f.build(parent, f'{name}[{i}]' ) for i,f in enumerate(self) ] )
        else:
            return ObjectList( [f.build(parent) for f in self] )


    def __init__(self, __root__=None, Factory=None):
        if __root__ is not None:
            if isinstance(__root__, FactoryList):
               __root__[:] = __root__.__root__[:]
            else:
                __root__[:] = [self.__cast_item(e, Factory) for e in __root__]
        else:
            __root__ = []
        super().__init__(__root__=__root__)
        
        if Factory is not None:
            self.__dict__['__Factory__'] = Factory
        
    @property
    def Factory(self):
        return self.__Factory__
 

    def __iter__(self):
        return iter(self.__root__)

    def __repr__(self): return self.__class__.__name__ +"("+repr(self.__root__) + ", "+ repr(self.Factory)+")"
    def __cast(self, other):
        return other.__root__ if isinstance(other, FactoryList) else [self.__cast_item(e, self.Factory) for e in other]

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
    
    def __lt__(self, other): return self.__root__ <  self.__cast(other)
    def __le__(self, other): return self.__root__ <= self.__cast(other)
    def __eq__(self, other): return self.__root__ == self.__cast(other)
    def __gt__(self, other): return self.__root__ >  self.__cast(other)
    def __ge__(self, other): return self.__root__ >= self.__cast(other)
    
    def __contains__(self, item): return item in self.__root__
    def __reversed__(self):
        for i in reversed(range(len(self))):
            yield self[i]

    def __len__(self): return len(self.__root__)
    def __getitem__(self, i): return self.__root__[i]

    def __setitem__(self, i, item): self.__root__[i] = self.__cast_item(item, self.Factory)
    def __delitem__(self, i): del self.__root__[i]

    def __add__(self, other):
        return self.__class__(self.__root__ + self.__cast(other), self.Factory)
    
    def __radd__(self, other):
        return self.__class__( self.__cast(other) + self.__root__, self.Factory)
    def __iadd__(self, other):
        if isinstance(other, FactoryList):
            self.__root__ += other.__root__
        else:
            self.__root__ += self.__cast(other)
        return self
    def __mul__(self, n):
        return self.__class__(self.__root__*n, self.Factory)
    __rmul__ = __mul__
    def __imul__(self, n):
        self.__root__ *= n
        return self
    def append(self, item): self.__root__.append(self.__cast_item(item, self.Factory))
    def insert(self, i, item): self.__root__.insert(i, self.__cast_item(item, self.Factory))

    def pop(self, i=-1): return self.__root__.pop(i)
    def remove(self, item): self.__root__.remove(item)
    def clear(self): self.__root__.clear()

    def copy(self, deep=False):
        copy_func = copy.deepcopy if deep else copy.copy 
        
        return self.__class__( copy_func(self.__root__), self.Factory)
    def count(self, item): return self.__root__.count(item)
    def index(self, item, *args): return self.__root__.index(item, *args)
    def reverse(self): self.__root__.reverse()
    def sort(self, *args, **kwds): self.__root__.sort(*args, **kwds)

    def extend(self, other):
        self.__root__.extend(self.__cast(other))



def _factory_list_constructor(loader, tag_suffix, node):
    if isinstance(node, yaml.SequenceNode):
        Factory = _get_factory_dict_constructor(tag_suffix)
        l = loader.construct_sequence( node, deep=True) 
        return FactoryList( l, Factory)
    else:
        raise ValueError(f"Expecting a collection for !DictFactory tag")
        
add_multi_constructor( "!FactoryList:", _factory_list_constructor)


