from ._core_base import (_BaseObject, _BaseProperty, ObjectIterator, ChildError,
        IOConfig, ksplit, BaseData,
        open_object, _get_class_dict)
from ._class_recorder import get_device_class, KINDS, get_class, record_class
from ._core_node import BaseNode, _NodeListing, parse_node_map
from ._core_interface import BaseInterface, _InterfaceListing, parse_interface_map
from ._core_com import BaseCom
from ._core_rpc import BaseRpc, _RpcListing, parse_rpc_map
from pydantic  import BaseModel, validator
from .. import io 

from typing import List, Optional, Any, Dict, Union, Type





class BaseDeviceConfig(_BaseObject.Config):
    kind: KINDS = KINDS.DEVICE.value
    type: str = "Base"
    com: Optional[BaseCom.Config] = None
    
    map_built: bool = False
    
    interface_map : Dict[str, Union[BaseInterface.Config, dict]] = None
    node_map : Dict[str, Union[BaseNode.Config, dict]] = None
    rpc_map : Dict[str, Union[BaseRpc.Config, dict]] = None
    
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
    
    class Config:
        validate_assignment = True

class BaseDeviceConfig(BaseDeviceConfig):
    device_map : Dict[str, Union[BaseDeviceConfig, dict]] = {}
    
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




def parse_device_map(parentClass, map):   
    for name, conf in map.items():
        if isinstance(conf, BaseModel): continue
        
        if isinstance(conf, str):
            conf = io.load_config(conf)
        elif 'cfgfile' in conf:
            tmp = IOConfig.parse_obj(conf)
            conf = io.load_config(tmp.cfgfile)
            conf.update(**tmp.dict(exclude=set(['cfgfile'])))
            
        try:
            prop = getattr(parentClass, name)
        except AttributeError:
            type_ = conf.get('type', None)
            if type_ is None:
                if isinstance(parentClass, BaseDevice):
                    # assume a default type for a device child of a device the parent type 
                    cls = parentClass
                else:
                    cls = parentClass.Device                
            else:
                cls = get_device_class(type_)
            
            if 'node_map' in conf: 
                parse_node_map(cls, conf['node_map'])
            if 'rpc_map' in conf: 
                parse_rpc_map(cls, conf['rpc_map'])
            if 'interface_map' in conf: 
                parse_interface_map(cls, conf['interface_map'])
            if 'device_map' in conf: 
                parse_device_map(cls, conf['device_map'])
            conf['map_built'] = True
            map[name] = cls.Config.parse_obj(conf)
        else:
            # TODO treat the node ?????
            newconf = {**prop._config.dict(), **conf}
            if 'node_map' in newconf: 
                parse_node_map(prop._cls, newconf['node_map'])
            if 'rpc_map' in newconf: 
                parse_rpc_map(prop._cls, newconf['rpc_map'])
            if 'interface_map' in newconf: 
                parse_interface_map(prop._cls, newconf['interface_map'])
            if 'device_map' in newconf: 
                parse_device_map(prop._cls, newconf['device_map'])
            newconf['map_built'] = True
            map[name] = prop._cls.Config.parse_obj(newconf)
                                    
                                                
    for subcls in parentClass.__mro__:
        for name, obj in subcls.__dict__.items():
            if isinstance(obj, _BaseProperty):
                if issubclass(obj._cls, BaseDevice):
                    if not name in map:
                        newconf = obj._config.copy(deep=True).dict()                      
                        if 'node_map' in newconf:
                            parse_node_map(obj._cls, newconf['node_map'] )
                        if 'rpc_map' in newconf:
                            parse_rpc_map(obj._cls, newconf['rpc_map'] )
                        if 'interface_map' in newconf:
                            parse_interface_map(obj._cls, newconf['interface_map'] )
                        if 'device_map' in newconf:
                            parse_device_map(obj._cls, newconf['device_map'] )
                        newconf['map_built'] = True
                        map[name] = obj._cls.Config.parse_obj(newconf) 
    
    
class DeviceProperty(_BaseProperty):    
    fbuild = None    
    
    def builder(self, func):
        """ Decorator for the interface builder """
        self.fbuild = func
        return self
    
    def get_config(self, parent):
        try:
            sconf = parent.config.device_map[self._name]
        except (KeyError, AttributeError):
            return self._config.copy(deep=True)
        else:
            return sconf
    
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
                      
class BaseDevice(_BaseObject, _NodeListing, _InterfaceListing, _RpcListing):
    Property = DeviceProperty
    Config = BaseDeviceConfig
    Interface = BaseInterface
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc    
    
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
        if config is  None:
            kwargs['map_built'] = True
            parse_device_map(cls, kwargs.setdefault('device_map', {}))
            parse_interface_map(cls, kwargs.setdefault('interface_map', {}))
            parse_node_map(cls, kwargs.setdefault('node_map', {}))
            parse_rpc_map(cls, kwargs.setdefault('rpc_map', {}))
            
        return super().parse_config(config, **kwargs)
        
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
    
        
class _DeviceListing:
    # provide a standard capability to have node has children with some method
    # in this context self is the parent 
    
    
    def _config_device_keys(self):
        return self.config.device_map.keys()
    
    def _config_device_constructor(self, name):
        try:
            deviceconf = self.config.device_map[name]
        except KeyError:
            raise ChildError(f"Unknown device {name}")
        return get_device_class(deviceconf.type).new    
    
    def _build_device(self, name):
        constructor = self._config_device_constructor(name)
        device = constructor(self, name, config=self.config.device_map[name])
        self.__dict__[name] = device 
        return device    
    
    parse_device_map = classmethod(parse_device_map)
    
    @classmethod
    def default_device_map(cls):
        return {}
    
    @property
    def devices(self) -> List[BaseDevice]:
        """ An iterator on devices """
        return ObjectIterator(self, self._build_device, self._config_device_keys())
        
    def get_device(self, name: str):
        """ get the device child 
        
        Args:
           name (str): device recorded name (attribute of parent)
           
        """
        try:
            #cached node
            device = self.__dict__[name]
        except KeyError:
            try:
                # static device, as property 
                device = object.__getattribute__(self, name)
            except AttributeError:
                device = self._build_device(name)                
            else:
                if not isinstance(device, BaseDevice):
                    raise ValueError(f"Unknown device {name}") 
        else:
            if not isinstance(device, BaseDevice):
                raise ValueError(f"Unknown device {name}")        
        return device
    
    def add_device(self, name, device: Union[BaseDevice, BaseDevice.Config, dict]):
        """ Add a device
        
        This will also change the manager config.device_map 
        
        Args:
            name (str): The name (attribute) of the device
                
                ::
                
                    parent.add_device('motor1', motor1)
                    parent.motor1 is motor1
            
            device (Device, Config , dict): A device object or a config to build the new device
        
        """    
        if isinstance(device, dict):
            type_ = device.get('type',None)
            if type_ is None:
                cls = self.Device
            else:
                cls = get_class(KINDS.DEVICE, type_)
            if name is None:
                raise ValueError("name is missing")                                
            device = cls.new(self, name, **device)
        elif isinstance(device, BaseModel):
            if name is None:
                raise ValueError("name is missing") 
            device = cls.new(self, name, config=device)
            
        
        if name is None:
            _, name = ksplit(device.key)
        
        if name in self.config.device_map and self.config.device_map[name] != device.config:
            raise ValueError("Device already exists inside its parent")
        elif name in self.__dict__:
            raise ValueError(f"attribute {name} is already taken")
        
        self.config.device_map[name] = device.config
        setattr(self, name, device)  
      
    def remove_device(self, name):
        """ Remove a device 
        
        This will remove also the configuration inside the config.device_map 
        An ValueError is raised if the device is not in the parent or if it has been defined 
        statisticaly on the class.
        
        Args:
            name (str) : the reference (the attribute) of the device
        """
        
        try:
            getattr(self.__class__, name)
        except AttributeError:
            if not name in self.config.device_map:
                raise ValueError("Unknown device {name!r}")
            
            del self.config.device_map[name]
            try:
                del self.__dict__[name]
            except KeyError:
                pass    
        else:
            raise ValueError("device {name!r} was defined inside the class")    
        
                
    
# Add the _DeviceListing  capability to the BaseDevice    
@record_class
class BaseDevice(BaseDevice, _DeviceListing):
    pass        
    
    
    
