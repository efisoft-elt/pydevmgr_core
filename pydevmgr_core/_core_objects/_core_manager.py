from ._core_base import (_BaseObject, _BaseProperty, ksplit, BaseData, kjoin,  open_object, ChildrenCapabilityConfig,
                            ChildrenCapability)

from ._core_device import BaseDevice 
from ._core_node import BaseNode
from ._core_rpc import BaseRpc  
from ._core_interface import BaseInterface  
from ._class_recorder import KINDS, get_class, record_class

from ._core_pydantic import _default_walk_set

from ._core_obj_dict import ObjDict
from pydantic import create_model 


                      
class ManagerConfig(_BaseObject.Config, ChildrenCapabilityConfig):
    kind: KINDS = KINDS.MANAGER.value
    type: str = "Base"

class ManagerProperty(_BaseProperty):    
    fbuild = None    
    def builder(self, func):
        """ Decorator for the interface builder """
        self.fbuild = func
        return self
    
    def __call__(self, func):
        """ The call is used has fget decorator """
        self.fbuild = func
        return self
    
    def _finalise(self, parent, device):
        # overwrite the fget, fset function to the node if defined         
        if self.fbuild:
            self.fbuild(parent, device)

def open_manager(cfgfile, path=None, prefix="", key=None, default_type=None, **kwargs):
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
    kwargs.setdefault("kind", KINDS.MANAGER)
    return open_object(
                cfgfile, 
                path=path, prefix=prefix, 
                key=key, default_type=default_type, 
                **kwargs
            ) 



class ManagerDict(ObjDict):
   class Config(ObjDict.Config):
        kinds = set([KINDS.MANAGER])
        default_kind = KINDS.MANAGER

@record_class        
class BaseManager(_BaseObject, ChildrenCapability):
    Property  = ManagerProperty
    Config = ManagerConfig
    Data = BaseData
    Device = BaseDevice
    Interface = BaseInterface
    Node = BaseNode
    Rpc = BaseRpc
    Dict = ManagerDict
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._localdata is None:
            self._localdata = {}
    

    @property
    def devices(self):
        return self.find( BaseDevice )
        # for obj in self.__dict__.values():
        #     if isinstance(obj, BaseDevice):
        #         yield obj
    
               
   

    def connect(self) -> None:
        """ Connect all devices """
        for device in self.devices:
            device.connect()
    
    def disconnect(self) -> None:
        """ disconnect all devices """
        for device in self.devices:
            device.disconnect()                
                
                    
    @classmethod
    def parse_config(cls, config, **kwargs):
        if isinstance(config, dict):
            kwargs = {**config, **kwargs}
            config = None
           
        return super().parse_config(config, **kwargs)
        
    def clear(self):
        """ clear all cashed intermediate objects """
        self._clear_all()
    
        
