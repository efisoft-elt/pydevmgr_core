import weakref
from ._core_base import (_BaseObject, _BaseProperty,
                        ChildError, IOConfig, ksplit, BaseData, 
                         ChildrenCapabilityConfig,  ChildrenCapability
                        )
                         
from ._class_recorder import get_interface_class, get_class, record_class, KINDS

from ._core_com import BaseCom
from ._core_node import BaseNode
from ._core_rpc import BaseRpc
from ._core_obj_dict import ObjDict

from .. import io
from typing import Optional, Iterable, Union, List, Dict, Callable
#  ___ _   _ _____ _____ ____  _____ _    ____ _____ 
# |_ _| \ | |_   _| ____|  _ \|  ___/ \  / ___| ____|
#  | ||  \| | | | |  _| | |_) | |_ / _ \| |   |  _|  
#  | || |\  | | | | |___|  _ <|  _/ ___ \ |___| |___ 
# |___|_| \_| |_| |_____|_| \_\_|/_/   \_\____|_____|
# 


class BaseInterfaceConfig(_BaseObject.Config, ChildrenCapabilityConfig):
    """ Config for a Interface """
    kind: KINDS = KINDS.INTERFACE.value
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

class InterfaceDict(ObjDict):
    class Config(ObjDict.Config):
        kinds = set([KINDS.INTERFACE])
        default_kind= KINDS.INTERFACE 



@record_class # we can record this type because it should work as standalone        
class BaseInterface(_BaseObject, ChildrenCapability):
    """ BaseInterface is holding a key, and is in charge of building nodes """    
    
    _subclasses_loockup = {} # for the recorder 
    
    Config = BaseInterfaceConfig
    Property = InterfaceProperty
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc   
    Dict = InterfaceDict
    
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] = None,            
           **kwargs
        ) -> None:        
        
        super().__init__(key, config=config, **kwargs)  
        if self._localdata is None:
            self._localdata = {}
    

    def clear(self):
        """ clear all cashed intermediate objects """
        self._clear_all()        

                    

                

    
