from .base import (BaseObject, BaseData)
from .decorators import finaliser 
from .node import BaseNode 
from .interface import BaseInterface
from .rpc import BaseRpc
from enum import Enum 


from typing import  Optional, Any 



class BaseDeviceConfig(BaseObject.Config):
    def cfgdict(self, exclude=set()):
        all_exclude = {*{}, *exclude}
        d = super().cfgdict(exclude=all_exclude)       
        return d
    
  
    

class BaseDevice(BaseObject):
    Config = BaseDeviceConfig
    Interface = BaseInterface
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc    
    
    def __enter__(self):
        try:
            self.disconnect()
        except (ValueError, RuntimeError, AttributeError):
            pass 
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False # if exception it will be raised 
    
    @classmethod
    def parse_config(cls, config, **kwargs):
        if isinstance(config, dict):
            kwargs = {**config, **kwargs}
            config = None
        return super().parse_config( config, **kwargs)
        
                        
    def connect(self):
        """ Connect device to client """
        raise NotImplementedError('connect method not implemented') 
    
    def disconnect(self):
        """ Disconnect device from client """
        raise NotImplementedError('disconnect method not implemented')    
    
    def is_connected(self):
        """ True if device connected """
        raise NotImplementedError('is_connected method not implemented') 
    
        
    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Device: prop() method is deprecated, use instead the pydevmgr_core.decorators.finaliser to decorate the object creation tunning', name, config_path, frozen_parameters)
        return finaliser( cls.Config(**kwargs) )  
