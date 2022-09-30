from .class_recorder import get_class, KINDS, get_factory
from .base import BaseFactory, BaseObject
from .io import  Tags,  add_multi_constructor
import yaml
from pydantic import Extra, validator, root_validator
from typing import Optional 


class ObjectFactory(BaseFactory):
    """ Generic Factory used to build pydevmgr object """

    kind: KINDS 
    type: str 
    class Config:
        extra = Extra.allow 
    
    @validator('type')
    def _check_object_type(cls, type_, values):
        get_class( values['kind'], type_)
        return type_
    
    __pydevmgr_config__ = ( (None,None), None)
    def __init__(self, *args, **kwargs):
        super().__init__(*args,  **kwargs)
        # dry parse the config, let it fail in case of error
        get_class(self.kind, self.type).Config.parse_obj( self )
    


    def build(self, parent: BaseObject = None, name: Optional[str]= None) -> BaseObject:
        Object = get_class(self.kind, self.type)
        config = Object.Config.parse_obj( self )

        return config.build(parent, name) 


def factory_constructor(loader, node):
    if isinstance(node, yaml.MappingNode):
        raw = loader.construct_mapping(node)
        
        new = ObjectFactory.parse_obj(raw) 
        return new
    else:
        raise ValueError(f"Expecting a mapping for {Tags.FACTORY} tag")
 


def _get_factory_from_tag_suffix(tag_suffix):
   
    if not tag_suffix:
        return ObjectFactory
    else:
        return get_factory(tag_suffix)

def object_constructor(loader, tag_suffix, node):
    Factory = _get_factory_from_tag_suffix(tag_suffix)
    if isinstance( node, yaml.MappingNode):
        raw = loader.construct_mapping(node, deep=True)
    else:
        raise ValueError("object flag expecting a map or a string")
    return Factory.parse_obj(raw)

add_multi_constructor( "!Factory:" , object_constructor)
add_multi_constructor( "!F:" , object_constructor)




