from .base import ( BaseParentObject, _BaseProperty, BaseData)

from .factory_object import ObjectFactory
                         
from .class_recorder import  record_class, KINDS, record_factory

from .node import BaseNode
from .rpc import BaseRpc
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


        
class InterfaceProperty(_BaseProperty):    
    fbuild = None
    def builder(self, func):
        """ Decorator for the interface builder """
        self.fbuild = func
        return self

    def __call__(self, func):
        """ The call is used has fget decorator """
        self.fbuild = func
        return self
    
    def _finalise(self, parent, interface):
        # overwrite the fget, fset function to the node if defined         
        if self.fbuild:
            self.fbuild(parent, interface)            



@record_class # we can record this type because it should work as standalone        
class BaseInterface(BaseParentObject):
    """ BaseInterface is holding a key, and is in charge of building nodes """    
    
    _subclasses_loockup = {} # for the recorder 
    
    Config = BaseInterfaceConfig
    Property = InterfaceProperty
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
    
    
