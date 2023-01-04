from enum import Enum
from typing import Optional 
from pydevmgr_core.base.register import KINDS, record_factory
from systemy import BaseFactory , get_factory_class
from pydantic import Extra, validator
from pydevmgr_core.base.base import BaseObject
# used to force kind to be a device
__all__ = ["ObjectFactory", "ManagerFactory", "DeviceFactory", 
           "InterfaceFactory", "NodeFactory", "RpcFactory"]

class ObjectFactory(BaseFactory):
    """ Generic Factory used to build pydevmgr object """

    kind: KINDS 
    type: str 
    class Config:
        extra = Extra.allow 
    
    @validator('type')
    def _check_object_type(cls, type_, values):
        get_factory_class( type_, kind=values['kind'])
        return type_
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args,  **kwargs)
        # dry parse the config, let it fail in case of error
        kw = self.dict(exclude=set(["type", "kind"]))
        Config = get_factory_class( self.type, kind=self.kind)
        Config.parse_obj( kw )
        
    def build_config(self):
        Config = get_factory_class( self.type, kind=self.kind)
        config = Config.parse_obj(self.dict(exclude=set(["kind", "type"])) )
        return config

    def build(self, parent: Optional[BaseObject] = None, name: Optional[str]= None) -> BaseObject:
        config = self.build_config()
        return config.build(parent, name) 

# used to force kind to be a manager
class MANAGERKIND(str, Enum):
    MANAGER = KINDS.MANAGER.value

@record_factory("Manager")
class ManagerFactory(ObjectFactory):
    """ A Factory for any type of manager 
    
    The manager is defined by the type string and must have been recorded before
    """
    kind: MANAGERKIND = MANAGERKIND.MANAGER


class DEVICEKIND(str, Enum):
    DEVICE = KINDS.DEVICE.value

@record_factory("Device", kind="Device")
class DeviceFactory(ObjectFactory):
    """ A Factory for any type of device 
    
    The device is defined by the type string and must have been recorded before
    """
    kind: DEVICEKIND = DEVICEKIND.DEVICE


# used to force kind to be a interface
class INTERFACEKIND(str, Enum):
    INTERFACE = KINDS.INTERFACE.value


@record_factory("Interface")
class InterfaceFactory(ObjectFactory):
    """ A factory for any kind of interface  

    The interface is defined from the type keyword and must have been properly recorded before
    """
    kind: INTERFACEKIND = INTERFACEKIND.INTERFACE

# used to force kind to be a node 
class NODEKIND(str, Enum):
    NODE = KINDS.NODE.value


@record_factory("Node")
class NodeFactory(ObjectFactory):
    """ A Factory for any type of node 
    
    The node is defined by the type string and must have been recorded before
    """
    kind: NODEKIND = NODEKIND.NODE


# used to force kind to be a rpc 
class RPCKIND(str, Enum):
    RPC = KINDS.RPC.value


@record_factory("Rpc")
class RpcFactory(ObjectFactory):
    kind: RPCKIND = RPCKIND.RPC


