from .base import (BaseObject,  BaseData)
from .decorators import finaliser
from .device import BaseDevice 
from .node import BaseNode
from .rpc import BaseRpc  
from .interface import BaseInterface  

from enum import Enum 

class ManagerConfig(BaseObject.Config ):
    ... 


class BaseManager(BaseObject):
    Config = ManagerConfig
    Data = BaseData
    Device = BaseDevice
    Interface = BaseInterface
    Node = BaseNode
    Rpc = BaseRpc
     

    @property
    def devices(self):
        return self.find( BaseDevice )
   

    def connect(self) -> None:
        """ Connect all devices """
        for device in self.devices:
            device.connect()
    
    def disconnect(self) -> None:
        """ disconnect all devices """
        for device in self.devices:
            device.disconnect()                
                
    def __enter__(self):
        try:
            self.disconnect()
        except (ValueError, RuntimeError, AttributeError):
            pass 
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False # False-> If exception it will be raised
    
    @classmethod
    def parse_config(cls, config, **kwargs):
        if isinstance(config, dict):
            kwargs = {**config, **kwargs}
            config = None
           
        return super().parse_config(config, **kwargs)
    
    @classmethod
    def prop(cls,  name: str = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Manager: prop() method is deprecated, use instead the pydevmgr_core.decorators.finaliser to decorate the object creation tunning', name, config_path, frozen_parameters)
        return finaliser( cls.Config(**kwargs) )      
