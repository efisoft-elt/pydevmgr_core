from pydevmgr_core.base.class_recorder import get_class, KINDS
from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import Optional, TypeVar, Generic 

from .io import load_config

GenVar = TypeVar('GenVar')
GenConfVar = TypeVar('GenConfVar')
FactoryListVar = TypeVar('FactoryListVar')



class _BaseModelGenConf(BaseModel):
    class Config:
        extra = "allow"

class GenConf(Generic[GenConfVar]):
    """ Parse a Model. If the input is a string it is interpreted as a path to a config file 

    The model is loaded from the config file which must have an absolute path or a path relative 
    to one of the path defined in the $CFGPATH env varaible 
    
    A Node input will be interpreted as an empty dictionary (Model built without arguments). It will 
    fail if model has required entries 
    Example: 

    ::
        
        form pydevmgr_core import BaseDevice, GenConf

        class Config(BaseDevice.Config):
            child :  GenConf[BaseDevice.Config] = BaseDevice.Config()

        c = Config( child={})
        c = Config( child="/path/to/my/file.yml")
        

    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        pass
    
    
    @classmethod
    def validate(cls, value, field: ModelField):
                    
        if field.sub_fields:
            if len(field.sub_fields)!=1:
                raise ValidationError(['to many field GenConf require and accept only one argument'], cls)
                
        

            Model = field.sub_fields[0]
            if isinstance( Model, ModelField):
                Model = Model.type_
            
            if not hasattr(Model, "parse_obj"):
                 raise ValueError(f"field of GenConf is not a BaseModel but a {type(Model)}")
        else:
            Model = _BaseModelGenConf
            
        if isinstance( value, str):
            value = load_config( value )
        # if value is None:
        #     return Model()
        return Model.parse_obj(value)

    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'




