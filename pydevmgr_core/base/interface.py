from .engine import BaseEngine
from .base import ( BaseParentObject,  BaseData)

from .factory_object import ObjectFactory
                         
from .class_recorder import  record_class, KINDS, record_factory

from .node import BaseNode
from .rpc import BaseRpc
from .decorators import finaliser
from enum import Enum 
from typing import Optional
#  ___ _   _ _____ _____ ____  _____ _    ____ _____ 
# |_ _| \ | |_   _| ____|  _ \|  ___/ \  / ___| ____|
#  | ||  \| | | | |  _| | |_) | |_ / _ \| |   |  _|  
#  | || |\  | | | | |___|  _ <|  _/ ___ \ |___| |___ 
# |___|_| \_| |_| |_____|_| \_\_|/_/   \_\____|_____|
# 


# used to force kind to be a interface
class INTERFACEKIND(str, Enum):
    INTERFACE = KINDS.INTERFACE.value


@record_factory("Interface")
class InterfaceFactory(ObjectFactory):
    """ A factory for any kind of interface  

    The interface is defined from the type keyword and must have been properly recorded before
    """
    kind: INTERFACEKIND = INTERFACEKIND.INTERFACE



class BaseInterfaceConfig(BaseParentObject.Config):
    """ Config for a Interface """
    kind: INTERFACEKIND = INTERFACEKIND.INTERFACE
    type: str = "Base"     


@record_class # we can record this type because it should work as standalone        
class BaseInterface(BaseParentObject):
    """ BaseInterface is holding a key, and is in charge of building nodes """    
    
    _subclasses_loockup = {} # for the recorder 
    
    Config = BaseInterfaceConfig
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc   
    
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] = None,            
           **kwargs
        ) -> None:        
        
        super().__init__(key, config=config, **kwargs)  
        if self._localdata is None:
            self._localdata = {}
    
    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Interface: prop() method is deprecated, use instead the pydevmgr_core.decorators.finaliser to decorate the object creation tunning', name, config_path, frozen_parameters)
        return finaliser( cls.Config(**kwargs) )  
