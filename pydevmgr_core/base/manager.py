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
    
