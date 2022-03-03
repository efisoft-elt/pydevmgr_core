from ._core_base import _BaseObject, _BaseProperty, ChildError, ksplit, BaseData, kjoin, _get_class_dict, open_object
from ._core_device import _DeviceListing, BaseDevice, parse_device_map
from ._core_node import BaseNode, parse_node_map, _NodeListing
from ._core_rpc import BaseRpc, parse_rpc_map, _RpcListing
from ._core_interface import BaseInterface, parse_interface_map, _InterfaceListing
from ._class_recorder import KINDS, get_class, record_class

from pydantic import BaseModel, validator
from typing import Dict, Union

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
                      
class ManagerConfig(_BaseObject.Config):
    kind: KINDS = KINDS.MANAGER.value
    type: str = "Base"
    map_built: bool=  False
    map_built: bool = False
    
    interface_map : Dict[str, Union[BaseInterface.Config, dict]] = {} 
    node_map : Dict[str, Union[BaseNode.Config, dict]] = {}
    rpc_map : Dict[str, Union[BaseRpc.Config, dict]] = {} 
    device_map : Dict[str, Union[BaseDevice.Config, dict]] = {}
        
    @validator('device_map', pre=True, always=True)
    def _validate_device_map(cls, map, values):
        if values.get('map_built', False):
            return map
        cls = _get_class_dict(values)

        # cls = get_class(values['kind'], values['type'])
        if map is None:
            map = cls.default_device_map()
        cls.parse_device_map(map)
        return map
    
    @validator('rpc_map', pre=True, always=True)
    def _validate_rpc_map(cls, map, values):
        if values.get('map_built', False):
            return map
        cls = _get_class_dict(values)

        # cls = get_class(values['kind'], values['type'])

        if map is None:
            map = cls.default_rpc_map()
        cls.parse_rpc_map(map)
        return map
    
    @validator('node_map', pre=True, always=True)
    def _validate_node_map(cls, map, values):
        if values.get('map_built', False):
            return map
        cls = _get_class_dict(values)

        # cls = get_class(values['kind'], values['type'])   
        if map is None:
            map = cls.default_node_map()     
        cls.parse_node_map(map)
        return map
    
    @validator('interface_map', pre=True, always=True)
    def _validate_interface_map(cls, map, values):
        if values.get('map_built', False):
            return map        
        
        cls = _get_class_dict(values)

        # cls = get_class(values['kind'], values['type'])
        
        if map is None:
            map = cls.default_interface_map()
        cls.parse_interface_map(map)
        return map        

    def cfgdict(self, exclude=set()):     
        
        all_exclude = {*{"map_built", "node_map", "rpc_map", "interface_map","device_map"}, *exclude}
        d = super().cfgdict(exclude=all_exclude)
        for map  in ('node_map', 'rpc_map',  'interface_map','device_map'):
            if map not in exclude:
                d[map] = {k:n.cfgdict() for k,n in getattr(self, map).items()}
        return d


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





@record_class        
class BaseManager(_BaseObject, _DeviceListing, _NodeListing, _RpcListing, _InterfaceListing):
    Property  = ManagerProperty
    Config = ManagerConfig
    Data = BaseData
    Device = BaseDevice
    Interface = BaseInterface
    Node = BaseNode
    Rpc = BaseRpc
    
    def __init__(self, *args, devices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if devices:
            for name, obj in devices.items():
                if isinstance(obj, BaseDevice):
                    self.__dict__[name] = obj
                    self.config.device_map[name] = obj.config
                elif isinstance(obj, BaseDevice.Config):
                    Device = get_class(obj.kind, obj.type)
                    self.__dict__[name]  = Device(kjoin( self.key, name), config=obj)
                    self.config.device_map[name] = obj
                elif isinstance(obj, dict):
                    try:
                        tpe = obj['type']
                    except KeyError:
                        raise ValueError('For device "{name}" the type is missing ')
                    try:
                        kind = obj['kind']
                    except KeyError:
                        raise ValueError('For device "{name}" the kind is missing ')
                    Device = get_class(kind, tpe)
                    config = Device.Config.from_cfgdict(obj)
                    self.__dict__[name]  = Device(kjoin( self.key, name), config=config)
                    self.config.device_map[name] = obj    
                
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
        if config is  None:
            kwargs['map_built'] = True
            parse_device_map(cls, kwargs.setdefault('device_map', {}))
            parse_interface_map(cls, kwargs.setdefault('interface_map', {}))
            parse_node_map(cls, kwargs.setdefault('node_map', {}))
            parse_rpc_map(cls, kwargs.setdefault('rpc_map', {}))
            
        return super().parse_config(config, **kwargs)
            
    
    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            try:
                return self._build_interface(attr)
            except ChildError:
                pass
            try:
                return self._build_node(attr)
            except ChildError:
                pass
            try:
                return self._build_rpc(attr)
            except ChildError:
                pass
            try:
                return self._build_device(attr)
            except ChildError:
                pass
            raise AttributeError(attr)            
        
    def clear(self):
        """ clear all cashed intermediate objects """
        self._clear_all()
    
        
