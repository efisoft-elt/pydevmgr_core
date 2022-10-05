from .base import (BaseParentObject, BaseData, open_object, ObjectFactory)
from .decorators import finaliser 
from .class_recorder import  KINDS,  record_class,  record_factory
from .node import BaseNode 
from .interface import BaseInterface
from .rpc import BaseRpc
from enum import Enum 


from typing import  Optional, Any 


# used to force kind to be a device
class DEVICEKIND(str, Enum):
    DEVICE = KINDS.DEVICE.value

@record_factory("Device", kind="Device")
class DeviceFactory(ObjectFactory):
    """ A Factory for any type of device 
    
    The device is defined by the type string and must have been recorded before
    """
    kind: DEVICEKIND = DEVICEKIND.DEVICE



class BaseDeviceConfig(BaseParentObject.Config):
    kind: DEVICEKIND = DEVICEKIND.DEVICE
    type: str = "Base"
    
    
    def cfgdict(self, exclude=set()):
        all_exclude = {*{}, *exclude}
        d = super().cfgdict(exclude=all_exclude)       
        return d
    
  
    
def open_device(cfgfile, path=None, prefix="", key=None):
    """ Open a device from a configuration file 

        
        Args:
            cfgfile: relative path to one of the $CFGPATH or absolute path to the yaml config file 
            key: Key of the created Device, if None one is taken from path 
            path (str, int, optional): 'a.b.c' will loock to cfg['a']['b']['c'] in the file. If int it will loock to the Nth
                                        element in the file
                                        
            prefix (str, optional): additional prefix added to the name or key

        Output:
            device (BaseDevice subclass) :tanciated Device class     
    """
    
    return open_object(cfgfile, path=path, prefix=prefix, key=key, Factory=DeviceFactory) 


@record_class
class BaseDevice(BaseParentObject):
    Config = BaseDeviceConfig
    Interface = BaseInterface
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
        
    @classmethod
    def new_com(cls, config: Config, com: Optional[Any] = None) -> Any:
        """ Create a new communication object for the device 
            
        Args:
           config: Config object of the Device Class to build a new com 
           com : optional, A parent com object used to build a new com if applicable  
           
        Return:
           com (Any): Any suitable communication object  
        """
        return com 
    
                        
    def connect(self):
        """ Connect device to client """
        raise NotImplementedError('connect method not implemented') 
    
    def disconnect(self):
        """ Disconnect device from client """
        raise NotImplementedError('disconnect method not implemented')    
    
    def is_connected(self):
        """ True if device connected """
        raise NotImplementedError('is_connected method not implemented') 
    
    def rebuild(self):
        """ rebuild will disconnect the device and create a new com """
        self.disconnect()
        self.clear()
        self._com = self.new_com(self._config)
    
        
    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Device: prop() method is deprecated, use instead the pydevmgr_core.decorators.finaliser to decorate the object creation tunning', name, config_path, frozen_parameters)
        return finaliser( cls.Config(**kwargs) )  
