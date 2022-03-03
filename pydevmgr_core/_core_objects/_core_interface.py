from ._core_base import (_BaseObject, _BaseProperty,  KINDS,
                          ObjectIterator, ChildError, IOConfig, ksplit, BaseData, 
                        _get_class_dict
                        )
                         
from ._class_recorder import get_interface_class, get_class, record_class

from ._core_com import BaseCom
from ._core_node import BaseNode, _NodeListing, parse_node_map
from ._core_rpc import BaseRpc, _RpcListing, parse_rpc_map
from .. import io
from typing import Optional, Iterable, Union, List, Dict, Callable
from pydantic import BaseModel, validator, Extra
#  ___ _   _ _____ _____ ____  _____ _    ____ _____ 
# |_ _| \ | |_   _| ____|  _ \|  ___/ \  / ___| ____|
#  | ||  \| | | | |  _| | |_) | |_ / _ \| |   |  _|  
#  | || |\  | | | | |___|  _ <|  _/ ___ \ |___| |___ 
# |___|_| \_| |_| |_____|_| \_\_|/_/   \_\____|_____|
# 


class BaseInterfaceConfig(_BaseObject.Config):
    """ Config for a Interface """
    kind: KINDS = KINDS.INTERFACE.value
    type: str = "Base"    
    map_built: bool = False
    node_map : Dict[str, Union[BaseNode.Config, dict]] = {}
    rpc_map : Dict[str, Union[BaseRpc.Config, dict]] = {} 
    
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
    
    
    def cfgdict(self, exclude=set()):                
        all_exclude = {*{"map_built", "node_map", "rpc_map"}, *exclude}
        d = super().cfgdict(exclude=all_exclude)
        for map  in ('node_map', 'rpc_map'):
            if map not in exclude:
                d[map] = {k:n.cfgdict() for k,n in getattr(self, map).items()}
        
        return d
        
    
    
    class Config: # this is the Config of BaseModel
        extra = Extra.forbid        


def parse_interface_map(parentClass, map):        
    for name, conf in map.items():
        if  isinstance(conf, BaseModel): continue
        
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
                cls = parentClass.Interface
            else:
                cls = get_interface_class(type_)
            
            if 'node_map' in conf: 
                parse_node_map(cls, conf['node_map'])
            if 'rpc_map' in conf: 
                parse_rpc_map(cls, conf['rpc_map'])
            conf['map_built'] = True
            map[name] = cls.Config.parse_obj(conf)
        else:
            # TODO treat the node ?????
            newconf = {**prop._config.dict(), **conf}
            if 'node_map' in newconf: 
                parse_node_map(prop._cls, newconf['node_map'])
            if 'rpc_map' in newconf: 
                parse_rpc_map(prop._cls, newconf['rpc_map'])
            newconf['map_built'] = True
            map[name] = prop._cls.Config.parse_obj(newconf)
                                    
                                              
    for subcls in parentClass.__mro__:
        for name, obj in subcls.__dict__.items():
            if isinstance(obj, _BaseProperty):
                if issubclass(obj._cls, BaseInterface):
                    if not name in map:
                        map[name] = obj._config.copy(deep=True).dict()                        
                        if 'node_map' in map[name]:
                            parse_node_map(obj._cls, map[name]['node_map'] )
                        if 'rpc_map' in map[name]:
                            parse_rpc_map(obj._cls, map[name]['rpc_map'] )
                        map[name]['map_built'] = True    
                        map[name] = obj._cls.Config.parse_obj(map[name]) 
    
    
    
def annotation2node(cls, PropertyClass, arg=None):
    if isinstance(PropertyClass, str):
        PropertyClass = getattr(cls, PropertyClass).prop
    
    if arg is None:
        def mk_kwargs(p):
            return p
        def ckeck(p):
            return isinstance (p, dict)
                                
    elif isinstance(arg, str):
        def mk_kwargs(p):
            if isinstance (p, dict):
                return p
            return {arg:p}
        def check(p):
            return True
        
    else:
        def mk_kwargs(plist):
            if isinstance (plist, dict):
                return plist
            
            return {k:p for k,p in zip(arg, plist)}
        def check(p):
            return True
        
    for a,p in cls.__annotations__.items():        
        if check(p):
            kwargs = mk_kwargs(p)
            setattr(cls, a, PropertyClass(a, **kwargs))    

def buildproperty(PropertyClass, arg):
    def builder(cls):
        annotation2node(cls, PropertyClass, arg)
        return cls
    return builder 
    
class InterfaceProperty(_BaseProperty):    
    fbuild = None
    def builder(self, func):
        """ Decorator for the interface builder """
        self.fbuild = func
        return self

    def get_config(self, parent):
        try:
            sconf = parent.config.interface_map[self._name]
        except (KeyError, AttributeError):
            return self._config.copy(deep=True)
        else:
            return sconf
                
    def __call__(self, func):
        """ The call is used has fget decorator """
        self.fbuild = func
        return self
    
    def _finalise(self, parent, interface):
        # overwrite the fget, fset function to the node if defined         
        if self.fbuild:
            self.fbuild(parent, interface)            
            
@record_class # we can record this type because it should work as standalone        
class BaseInterface(_BaseObject,  _NodeListing, _RpcListing):
    """ BaseInterface is holding a key, and is in charge of building nodes """    
    
    _subclasses_loockup = {} # for the recorder 
    
    Config = BaseInterfaceConfig
    Property = InterfaceProperty
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
    
    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:           
            try:
                return self._build_node(attr)
            except ChildError:
                pass
            try:
                return self._build_rpc(attr)
            except ChildError:
                pass
            raise AttributeError(attr)            
                
    def clear(self):
        """ clear all cashed intermediate objects """
        self._clear_all()        

                    
        
class _InterfaceListing:
    # provide a standard capability to have node has children with some method
    # in this context self is the parent 
    
    def _config_interface_keys(self):
        return self.config.interface_map.keys()
    
    def _config_interface_constructor(self, name):
        try:
            interfaceconf = self.config.interface_map[name]
        except KeyError:
            raise ChildError(f"Unknown interface {name}")
        return get_interface_class(interfaceconf.type).new    
        
    def _build_interface(self, name):
        constructor = self._config_interface_constructor(name)
        interface = constructor(self, name, config=self.config.interface_map[name])
        self.__dict__[name] = interface 
        return interface
    
    parse_interface_map = classmethod(parse_interface_map)        
    
    @classmethod
    def default_interface_map(cls):
        return {}
    
    
    @property
    def interfaces(self) -> List[BaseInterface]:
        return ObjectIterator(self, self._build_interface, self._config_interface_keys())
        
    def get_interface(self, name: str) -> BaseInterface:
        try:
            #cached node
            interface = self.__dict__[name]
        except KeyError:
            try:
                # static interface, as property 
                interface = object.__getattribute__(self, name)
            except AttributeError:
                interface = self._build_interface(name)
            else:
                if not isinstance(interface, BaseInterface):
                    raise ValueError(f"Unknown interface {name}")
        else:
            if not isinstance(interface, BaseInterface):
                raise ValueError(f"Unknown interface {name}")           
        return interface
        
    def add_interface(self, name, interface: Union[BaseInterface, BaseInterface.Config, dict]):
        """ Add a interface
        
        This will also change the manager config.interface_map 
        
        Args:
            name (str): The name (attribute) of the interface
                
                ::
                
                    parent.add_interface('motor1', motor1)
                    parent.motor1 is motor1
            
            interface (Interface, Config , dict): A interface object or a config to build the new interface
        
        """    
        if isinstance(interface, dict):
            type_ = interface.get('type',None)
            if type_ is None:
                cls = self.Interface
            else:
                cls = get_class(KINDS.INTERFACE, type_)
            if name is None:
                raise ValueError("name is missing")                                
            interface = cls.new(self, name, **interface)
        elif isinstance(interface, BaseModel):
            if name is None:
                raise ValueError("name is missing") 
            interface = cls.new(self, name, config=interface)
            
        
        if name is None:
            _, name = ksplit(interface.key)
        
        if name in self.config.interface_map and self.config.interface_map[name] != interface.config:
            raise ValueError("Interface already exists inside its parent")
        elif name in self.__dict__:
            raise ValueError(f"attribute {name} is already taken")
        
        self.config.interface_map[name] = interface.config
        setattr(self, name, interface)              

    def remove_interface(self, name):
        """ Remove a interface 
        
        This will remove also the configuration inside the config.interface_map 
        An ValueError is raised if the interface is not in the parent or if it has been defined 
        statisticaly on the class.
        
        Args:
            name (str) : the reference (the attribute) of the interface
        """
        
        try:
            getattr(self.__class__, name)
        except AttributeError:
            if not name in self.config.interface_map:
                raise ValueError("Unknown interface {name!r}")
            
            del self.config.interface_map[name]
            try:
                del self.__dict__[name]
            except KeyError:
                pass    
        else:
            raise ValueError("interface {name!r} was defined inside the class")    
        
                

interfaceproperty = BaseInterface.prop
    
