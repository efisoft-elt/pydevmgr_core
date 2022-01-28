from typing import Any,  Tuple, Optional, List, Dict, Union, Type
from pydantic import BaseModel, Extra
from ._class_recorder import get_class
from ._core_model_var import StaticVar
from enum import Enum 
import yaml
from ..io import ioconfig, load_yaml, load_config


class KINDS(str, Enum):
    PARSER = "Parser"
    NODE = "Node"
    RPC = "Rpc"
    DEVICE = "Device"
    INTERFACE = "Interface"
    MANAGER = "Manager"
    


class IOConfig(BaseModel):
    """ model for cfgfile definition """    
    cfgfile: str = ""
    class Config:
        extra = Extra.allow
    
class BaseConfig(BaseModel):
    kind: KINDS = ""
    type: str = ""
    version: str = "" # version of the configuration file 
    class Config: # this is the Config of BaseModel
        extra = Extra.forbid
        validate_assignment = True    
        use_enum_values = True 
    
    @classmethod
    def from_cfgfile(cls, cfgfile, path: str = ''):
        """ Create the config object from a yaml config file 
        
        Args:
            cfgfile (str): Configuration file relative to one of $CFGPATH or absolute path 
            path (str, optional): path where to find the root configuration. if "" the config file 
                 contains the root. For instance 'a.b.c' will look at configuration in cfg['a']['b']['c']
        """
        config = load_config(cfgfile)
        for p in (s for s in  path.split('.') if s):
            config = config[p]
        return cls.from_cfgdict(config)                    
    
    @classmethod 
    def from_cfgdict(cls, config_dict):
        """ Create the config object from python dictionary """
        return cls.parse_obj(config_dict)
         
    
    def cfgdict(self, exclude=set()):
        """ Write the config to a dictionary as it is red from from_cfgdict """
        d = self.dict(exclude_unset=True, exclude=exclude)
        return d

def open_object(
        kind, 
        cfgfile, 
        path: Optional[str] = None, 
        prefix: str = '', 
        key: Optional[str]= None, *args, **kwargs
    ):     
    if path is None:
        # get the first key 
        allconf = load_config(cfgfile)
        path = next(iter(allconf))
        allconf = allconf[path]            
    else:
        allconf = load_config(cfgfile)
        for p in (s for s in  path.split('.') if s):
            allconf = allconf[p]
    tpe = allconf['type']
    
    Device = get_class(kind, tpe)
    config = Device.Config.from_cfgdict(allconf)  
    if key is None and path: 
        _, name = ksplit(path)           
        key = kjoin(prefix, name)
    return Device(key, *args, config=config, **kwargs)
        
class BaseData(BaseModel):
    # place holder for Data class 
    key: StaticVar[str] = ""

class ChildError(ValueError):
    """ Error raise when a parent try to reach a child object (interface, node, rpc, ...) and cannot find it"""
    pass

def load_yaml_config(yaml_payload: str, path: Optional[Union[str, tuple]] = None) -> Tuple[Type,BaseConfig]:
    """ Load a yaml configuration and pare it in the right configuration object 
    
    The Config class used is localised thanks to the `kind` and `type` string argument inside the yaml
    If the class is not recognised an Exception is raised.
    
    Args:
        yaml_payload (str):  The yaml string payload 
        path (optional, str, tuple):  A string or tuple representing a path through the wanted object 
    
    Returns:
        cls (Type):  The object Class 
        config (BaseModel):  The parsed configuration 
    """
    payload = yaml.load(yaml_payload, Loader=ioconfig.YamlLoader)
    if path is not None:
        if isinstance(path , str):
            path = [path]
        for p in path:
            payload = payload[p]
    
    return load_dict_config(payload)
    
def load_dict_config(payload: dict)-> Tuple[Type,BaseConfig]:
    try:
        kind = payload['kind']
    except KeyError:
        raise ValueError('"kind" attribute missing')
    try:
        type = payload['type']
    except KeyError:
        raise ValueError('"type" attribute missing')    
    cls = get_class(kind, type)
    return cls, cls.Config.parse_obj(payload)

def build_yaml(yaml_payload, key: Optional[str]=None, *args, **kwargs):
    """ Build and return an object from its yaml configuration payload """
    cls, config = load_yaml_config(yaml_payload)
    return cls(key, *args, config=config, **kwargs)

def load_and_build( cfgfile: str, key: Optional[str] = None, *args, **kwargs):
    """ Load a config file and build the conrespoding object defined by kind and type config parameters """
    payload = load_config(cfgfile)
    
    cls, config = load_dict_config(payload)
    return cls(key, *args, config=config, **kwargs)
    
def kjoin(*args) -> str:
    """ join key elements """
    return ".".join(a for a in args if a)

def ksplit(key: str) -> Tuple[str,str]:
    """ ksplit(key) ->  prefix, name
    
    >>> ksplit('a.b.c')
    ('a.b', 'c')
    """
    s, _, p = key[::-1].partition(".")
    return p[::-1], s[::-1]

def reconfig(ConfigClass: Type, config: BaseConfig, kwargs: dict) -> BaseConfig:    
    if config is None:
        return ConfigClass.parse_obj(kwargs)
    if isinstance(config, dict):
        return ConfigClass.parse_obj(dict(config, **kwargs))    
    return config


_key_counter = {}
def new_key(config):
    k = config.type+config.kind
    c = _key_counter.setdefault(k,0)
    c += 1
    _key_counter[k] = c
    return f'{k}{c:03d}'


class _BaseProperty:    
    """ A Property is basically calling a constructor with dynamical and static arguments 
    
    The Property has the followind signature : 
        Property(constructor, name, *args, config=None, **kwargs)
        
    The constructor is called with the following signature
        constructor( parent , name, *args, config=config, **kwargs)
    
    So it must have at least twho positional arguments a config keyword argument and 
    optional keyword arguments  
    
    """    
    def __init__(self, cls, constructor, name, *args, config=None,  **kwargs):
        
        self._cls = cls 
        self._constructor = constructor
        self._name = name         
        
        self._config = config        
        self._args = args
        self._kwargs = kwargs
        
    @property
    def congig(self):
        return self._config
            
    def _finalise(self, parent, obj):
        pass
    
    def __get__(self, parent, clp=None):
        if parent is None:
            return self 
        # try to retrieve the node directly from the parent __dict__ where it should 
        # be cached. If no boj cached create one and save it/ 
        # if _name is the same than the attribute name in class, this should be called only ones                
        try:
            obj = parent.__dict__[self]
        except KeyError:
            name, obj = self.new(parent)     
            # store in parent with the name 
            parent.__dict__[self] = obj        
        return obj
                
    def get_config(self, parent):
        """ return configuration from parent object """
        # this has to be implemented for each kinds 
        return self._config.copy(deep=True)
                
    def new(self, parent):     
        config = self.get_config(parent)
        if self._name is None:
            name = new_key(config)
            
            #name = config.kind+str(id(config))
        else:
            name = self._name                            
        obj = self._constructor(parent, name, *self._args, config=config, **self._kwargs)            
        self._finalise(parent, obj)
        return name, obj 
        

class _BaseObject:
    __all_cashed__ = False
    Config = BaseConfig
    Property = _BaseProperty    
    _config = None
            
    def __init__(self, 
          key: Optional[str] = None,  
          config: Optional[Config] = None, *,          
          localdata: Optional[dict] = None, 
          **kwargs 
        ) -> None:
        self._config = self.parse_config(config, **kwargs)                            
        if key is None: 
            key = new_key(self._config)
        
        self._key = key     
        self._localdata = localdata
        
    def __repr__(self):
        return "<{} key={!r}>".format(self.__class__.__name__, self._key)
    
    
    @classmethod
    def parse_config(cls, __config__=None, **kwargs):
        if __config__ is None:
            return cls.Config(**kwargs)
        if isinstance(__config__ , cls.Config):
            return __config__
        if isinstance(__config__, dict):
            return cls.Config( **{**__config__, **kwargs} )
        raise ValueError(f"got an unexpected object for config : {type(__config__)}")
            
    @classmethod
    def new_args(cls, parent, config: Config) -> dict:
        """ build a dictionary of dynamical variables inerited from a parent """
        return dict( localdata = getattr(parent, "localdata", None) )
            
    @classmethod
    def new(cls, parent, name, config=None, **kwargs):
        """ a base constructor for BaseNode 
        
        parent must have the .key attribute 
        """        
        # here shall be implemented something to deal with config, it might be that config it comming
        # from the parent.config like node_map, etc ...
        config = cls.parse_config(config, **kwargs)
        if name is None:
            name = new_key(config)                                
        return cls(kjoin(parent.key, name), config=config, **cls.new_args(parent, config))
    
    @classmethod
    def prop(cls, name: Optional[str] = None, **kwargs):
        """ Return an object  property  to be defined in a class 
        
        Exemple:
           
           ::
           
                def MyDevice(BaseDevice):
                   ref_temperature = StaticNode.prop(value=22.0
                
                MyDevice().ref_temperature.get()   
        """
        config = cls.Config.parse_obj(kwargs)                
        return cls.Property(cls, cls.new, name, config=config)
    
    @classmethod
    def from_cfgfile(cls, 
            cfgfile: str, 
            path: Optional[str] = None, 
            prefix: str = '', 
            key: Optional[str]= None, 
            *args, **kwargs
        ) -> '_BaseObject':
        """ Create the object from a configuration file 
        
        Args:
            cfgfile (str): Path to the config file, shall be relative to one of the $CFGPATH or absolute
                     path
            path (None, str, False)"" the hierarchique path where to find the config data inside the file 
                    for instance 'a.b.c' will loock at cfg['a']['b']['c'] from the loaded config file 
                    If "" the config file define the device configuration from its root 
                    If None the first item of the config file is taken 
            prefix (str, optional): add a prefix to the path name to build the device key. 
                    It is used only if key is None otherwhise ignored
            key (str, Optional): key of the device, if not given this is built from the path suffix and
                    the optional prefix
        """
        
                        
        if path is None:
            # get the first key 
            allconf = load_config(cfgfile)
            path = next(iter(allconf))            
        else:
            allconf = load_config(cfgfile)
            for p in (s for s in  path.split('.') if s):
                allconf = allconf[p]
                
        config = cls.Config.from_cfgdict(allconf)            
        if key is None and path: 
            _, name = ksplit(path)           
            key = kjoin(prefix, name)
                                        
        return cls(key, *args, config=config, **kwargs)
    
        
    @property
    def key(self):
        """ key """
        return self._key
    
    @property
    def config(self):
        """  config """
        return self._config
    
    @property
    def localdata(self):
        """ localdata dictionary """
        return self._localdata
        
    @property
    def name(self):
        return ksplit(self._key)[1]    
    
    @classmethod
    def _builtin_objects(cls, SubCls=None):
        SubCls = SubCls or _BaseObject
        d = {}
        for sub in cls.__mro__:
            for k,v in sub.__dict__.items():
                if isinstance(v, (_BaseProperty)):
                    if issubclass(v._cls, SubCls):
                        d[k] = v._cls
        return d
                    
    def _cash_all(self):
        """ cash all child _BaseProperty to real Objects """
        if not self.__all_cashed__:
            for sub in self.__class__.__mro__:
                for k,v in sub.__dict__.items():
                    if isinstance(v, (_BaseProperty)):
                        getattr(self, k)
            self.__all_cashed__ = True
    
    def _clear_all(self):
        """ clear all cashed intermediate objects """
        for k,v in list(self.__dict__.items()):
            if isinstance(v, (_BaseObject)):
                self.__dict__.pop(k)
        self.__all_cashed__ = False



class ObjectIterator:
    _iterator = None
    def __init__(self, obj, constructor, names):
        self._obj = obj
        self._constructor = constructor
        self._names = names 
    
    def __iter__(self):
        self._iterator = iter(self._names)
        return self
    
    def __next__(self):
        name = next(self._iterator)
        try:
            return object.__getattribute__(self._obj, name)
        except AttributeError:
            return self._constructor(name)
        
    def __getitem__(self, name):
        
        try:
            return object.__getattribute__(self._obj, name)
        except AttributeError:
            return self._constructor(name)
    
    def __call__(self) -> List:
        return list(self)
    
    def names(self) -> List:
        return list(self._names)
       
       
class _Old_ObjectIterator_To_delete:
    _iterator = None
    def __init__(self, map: dict, classes: Union[Type,Tuple[Type]]):
        self._map = map
        self._classes = classes 
    
    def __iter__(self):
        self._iterator = iter(self._map.items())
        return self
    
    def __next__(self):
        k,v = next(self._iterator)
        if isinstance(v, self._classes):
            return v
        return self.__next__()
    
    def __getitem__(self, item):
        v = self._map[item]
        if isinstance(v, self._classes):
            return v 
        raise KeyError(item)
    
    def __call__(self) -> List:
        return list(self)
    
    def names(self) -> List:
        return [k for k,v in self._map.items() if isinstance(v, self._classes)]
       
def _collect_config_properties(cls, prop_kind):
    for sub in cls.__mro__:
        for k,v in sub.__dict__.items():
            if isinstance(v, (_BaseProperty)):
                if v._config.kind is prop_kind:
                    yield k, v._config





                       
        
