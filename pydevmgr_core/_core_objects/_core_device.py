from ._core_base import (_BaseObject, _BaseProperty, ObjectIterator, ChildError,
        IOConfig, ksplit, BaseData,
        open_object, 
        
        ChildrenCapability, ChildrenCapabilityConfig

        )
from ._class_recorder import get_device_class, KINDS, get_class, record_class
from ._core_node import BaseNode 
from ._core_interface import BaseInterface
from ._core_com import BaseCom
from ._core_rpc import BaseRpc

from ._core_obj_dict import ObjDict

from .. import io 

from typing import List, Optional, Any, Dict, Union, Type





class BaseDeviceConfig(_BaseObject.Config, ChildrenCapabilityConfig):
    kind: KINDS = KINDS.DEVICE.value
    type: str = "Base"
    com: Optional[BaseCom.Config] = None
    
    
    def cfgdict(self, exclude=set()):
        all_exclude = {*{}, *exclude}
        d = super().cfgdict(exclude=all_exclude)       
        return d
    
  
    
def open_device(cfgfile, path=None, prefix="", key=None, default_type=None, **kwargs):
    """ Open a device from a configuration file 

        
        Args:
            cfgfile: relative path to one of the $CFGPATH or absolute path to the yaml config file 
            key: Key of the created Manager 
            path (str, int, optional): 'a.b.c' will loock to cfg['a']['b']['c'] in the file. If int it will loock to the Nth
                                        element in the file
            prefix (str, optional): additional prefix added to the name or key

        Output:
            device (BaseDevice subclass) :tanciated Device class     
    """
    kwargs.setdefault("kind", KINDS.DEVICE)

    return open_object(cfgfile, path=path, prefix=prefix, key=key, default_type=default_type, **kwargs) 




class DeviceProperty(_BaseProperty):    
    fbuild = None    
    
    def builder(self, func):
        """ Decorator for the interface builder """
        self.fbuild = func
        return self
     
   
    def __call__(self, func):
        """ The call is used has fbuild decorator 
        
        this allows to do
        
        ::
            
            class MyManager(BaseManager):
                @MyDevice.prop('motor2')
                def motor2(self, motor):
                    # do somethig
                    
        """
        self.fbuild = func
        return self
    
    def _finalise(self, parent, device):
        # overwrite the fget, fset function to the node if defined         
        if self.fbuild:
            self.fbuild(parent, device)  



class DeviceDict(ObjDict):
    class Config(ObjDict.Config):
        kinds = set([KINDS.DEVICE])

        default_kind = KINDS.DEVICE

@record_class
class BaseDevice(_BaseObject, ChildrenCapability):
    Property = DeviceProperty
    Config = BaseDeviceConfig
    Interface = BaseInterface
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc    
    Dict = DeviceDict 
    
    _com = None                
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] = None,
           com: Optional[Any] = None,             
           **kwargs
        ) -> None:        
        
        super().__init__(key, config=config, **kwargs)  
        if self._localdata is None:
            self._localdata = {}
        self._com = self.new_com(self._config, com)


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
    
        

        
    def clear(self):
        """ clear all cashed intermediate objects """
        self._clear_all()  
            
    @property
    def com(self):
        return self._com
        
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
    
        

