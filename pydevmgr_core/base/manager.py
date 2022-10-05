from .base import (BaseParentObject,  BaseData,  open_object, ObjectFactory)
from .decorators import finaliser
from .device import BaseDevice 
from .node import BaseNode
from .rpc import BaseRpc  
from .interface import BaseInterface  
from .class_recorder import KINDS,  record_class, record_factory

from enum import Enum 

# used to force kind to be a manager
class MANAGERKIND(str, Enum):
    MANAGER = KINDS.MANAGER.value

@record_factory("Manager")
class ManagerFactory(ObjectFactory):
    """ A Factory for any type of manager 
    
    The manager is defined by the type string and must have been recorded before
    """
    kind: MANAGERKIND = MANAGERKIND.MANAGER



class ManagerConfig(BaseParentObject.Config ):
    kind: MANAGERKIND = MANAGERKIND.MANAGER
    type: str = "Base"
     


def open_manager(cfgfile, path=None, prefix="", key=None):
    """ Open a manager from a configuration file 

        
        Args:
            cfgfile: relative path to one of the $CFGPATH or absolute path to the yaml config file 
            key: Key of the created Manager 
            path (str, int, optional): 'a.b.c' will loock to cfg['a']['b']['c'] in the file. If int it will loock to the Nth
                                        element in the file
            prefix (str, optional): additional prefix added to the name or key

        Output:
            manager (BaseManager subclass) :tanciated Manager class     
    """
    return open_object(
                cfgfile, 
                path=path, prefix=prefix, 
                key=key, Factory=ManagerFactory     
            ) 
    


@record_class        
class BaseManager(BaseParentObject):
    Config = ManagerConfig
    Data = BaseData
    Device = BaseDevice
    Interface = BaseInterface
    Node = BaseNode
    Rpc = BaseRpc
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._localdata is None:
            self._localdata = {}
    

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
