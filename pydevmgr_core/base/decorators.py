import weakref
from typing import  Optional, Union, Type


from pydevmgr_core.base.base import BaseFactory, BaseObject, __Decorator__



__all__ = [
"BaseDecorator", 
"getter", 
"setter",
"caller", 
"finaliser", 
]


class BaseDecorator(__Decorator__):
    method = None
    def __init__(self, factory: Union[BaseFactory, Type[BaseObject]]) -> None:

        if isinstance(factory, type) and issubclass( factory, BaseObject):
            factory = factory.Config()
        self.factory = factory
    
    def __get__(self, parent, cls):
        if parent is None:
            return self
        obj = self.factory.__get__(parent, cls)
        self._alterate(parent, obj)
        return obj
    
    def _alterate(self, parent, obj):
        raise NotImplementedError('_alterate')

    def __set_name__(self, parent, name):
        self.factory.__set_name__(parent, name)
    
    def __call__(self, func):
        self.method = func
        return self



class BaseNodeDecorator(BaseDecorator):
    def __init__(self, 
            factory:  Union[BaseFactory, Type[BaseObject]], 
            include_object: bool= False
        ) -> None:
        super().__init__(factory)
        self.include_object = include_object

class getter(BaseNodeDecorator):    
    def _alterate(self, parent, obj):
        if not self.method:
            return 
        
        parent_wr = weakref.ref(parent)
        if self.include_object:
            def fget(*args, **kwargs):
                return self.method(parent_wr(), obj, *args, **kwargs)
        else:
            def fget(*args, **kwargs):
                return self.method(parent_wr(), *args, **kwargs)
        obj.fget = fget 

class setter(BaseNodeDecorator):
    def _alterate(self, parent, obj):
        if not self.method:
            return 

        parent_wr = weakref.ref(parent)
        if self.include_object:
            def fset(*args, **kwargs):
                return self.method(parent_wr(), obj, *args, **kwargs)
        else:
            def fset(*args, **kwargs):
                return self.method(parent_wr(), *args, **kwargs)
        obj.fset = fset


class caller(BaseNodeDecorator):
    def _alterate(self, parent, obj):
        if not self.method:
            return 

        parent_wr = weakref.ref(parent)
        if self.include_object:
            def fcall(*args, **kwargs):
                return self.method(parent_wr(), obj, *args, **kwargs)
        else:
            def fcall(*args, **kwargs):
                return self.method(parent_wr(), *args, **kwargs)
        obj.fcall = fcall 


class finaliser(BaseDecorator):
    def _alterate(self, parent, obj):
        if not self.method:
            return 

        self.method(parent, obj)
   

