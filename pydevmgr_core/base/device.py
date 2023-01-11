from .base import (BaseObject, BaseData)
from .node import BaseNode 
from .interface import BaseInterface
from .rpc import BaseRpc

#  ____  _______     _____ ____ _____ 
# |  _ \| ____\ \   / /_ _/ ___| ____|
# | | | |  _|  \ \ / / | | |   |  _|  
# | |_| | |___  \ V /  | | |___| |___ 
# |____/|_____|  \_/  |___\____|_____|
                                    


class BaseDeviceConfig(BaseObject.Config):
    def cfgdict(self, exclude=set()):
        d = super().cfgdict(exclude=exclude)       
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
                        
    def connect(self):
        """ Connect device to client """
        raise NotImplementedError('connect method not implemented') 
    
    def disconnect(self):
        """ Disconnect device from client """
        raise NotImplementedError('disconnect method not implemented')    
    
    def is_connected(self):
        """ True if device connected """
        raise NotImplementedError('is_connected method not implemented') 
    

