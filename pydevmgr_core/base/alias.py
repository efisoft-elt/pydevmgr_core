from typing import Any
from systemy import BaseFactory

from .register import register 
from .object_path import BasePath, PyPath

@register
class Alias(BaseFactory):
    """ Alias """
    target: PyPath
    def __init__(self, target):
        super().__init__(target=target) 

    @classmethod
    def parse_obj(cls, obj: Any) -> 'Alias':
        if isinstance( obj, dict):
            return super().parse_obj(obj)
        else:
            return super().parse_obj( {'target':obj})
    def build(self, parent=None, name=None):
        if parent is None:
            raise ValueError("Alias needs a parent object")
        return self.target.resolve( parent )
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, value: Any) -> 'Alias':
        if isinstance( value, (str, BasePath)):
            value = {"target":value} 
        return super().validate(value)
