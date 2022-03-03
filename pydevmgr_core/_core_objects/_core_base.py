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
    true_type: Optional[Type] = None
    
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
         
    
    def cfgdict(self, exclude: set =set()):
        """ Write the config to a dictionary as it is red from from_cfgdict """
        exclude.add('true_type')
        d = self.dict(exclude_unset=True, exclude=exclude)
        return d

def _path_walk(d, path):
    if isinstance(path, int):
        # get the first key
        
        if hasattr(d, "keys"):
            k = list(d.keys())[path]
            return d[k]
        else:
            return d[path]
   
    if path:
        for p in (s for s in  path.split('.') if s):
            d = d[p]
    return d

def _get_class_dict( d, default_type: Optional[Union[str, Type]] = None):

    try:
        kind = d['kind']
    except KeyError:
        raise ValueError('"kind" attribute missing')
    
    tt = d.get('true_type', None)
    if tt: 
        return tt
    
    try:
        st = d['type']
    except KeyError:
        raise ValueError('"type" attribute missing')    

    try:
        return get_class(kind, st)
    except ValueError as e:
        if default_type:
            if isinstance(default_type, type):
                return default_type
            return get_class(kind, default_type)
        raise e


def _get_class_config( c, default_type: Optional[Union[str, Type]] = None):
    if c.true_type:
        return c.true_type
    try:
        return get_class(c.kind, c.type)
    except ValueError as e:
        if default_type:
            if isinstance(default_type, type):
                return default_type
            return get_class(c.kind, default_type)
        raise e
  




def open_class(
        cfgfile: str, 
        path: Optional[Union[str, int]] = None, 
        default_type: Optional[str] = None,
        **kwargs
        ):
    """ open a pydevmgr class and configuration object from a config file 

    Args:
        cfgfile: relative to on of the $CFPATH or absolute path to yaml config file 
        kind (optional, str): object kind as enumerated in KINDS ('Manager', 'Device', 'Interface', 'Node', 'Rpc')
            if None look inside the configuration file and raise error if not defined. 
        
        path (optional, str, int): an optional path to find the configuration inside the config file 
             'a.b.c' will go to cfg['a']['b']['c']
             If an integer N will get the Nth element of the cfgfile 

        default_type (optional, str): A default type if no type is defined in the configuration file
            If default_type is None and no type is found an error is raised 

    Returns:
        ObjClass :  An pydevmgr Object class (Manager, Device, Node, Rpc, Interface)
        config : An instance of the config (BaseModel object) 
    """
    allconf = load_config(cfgfile)
        
    allconf = _path_walk(allconf, path)
    
    allconf.update( kwargs )
    
    try:
        kind = allconf['kind']
    except KeyError:
        raise ValueError("Configuration has no 'kind' defined")

    tpe = allconf.get('type', default_type)
    if not tpe:
        raise ValueError(f"Cannot resolve {kind} type")
    Object = get_class(kind, tpe)
    allconf['true_type'] = Object
    # config = Object.parse_config(allconf) 
    config = Object.Config.from_cfgdict(allconf)
    return Object, config

def open_object(
        cfgfile,
        key: Optional[str]= None, 
        path: Optional[Union[str, int]] = None, 
        prefix: str = '', 
        default_type: Optional[str] = None, 
        **kwargs
    ):
    """ open an object from a configuration file 
    Args:
        cfgfile: relative to on of the $CFPATH or absolute path to yaml config file 
        kind (optional, str): object kind as enumerated in KINDS ('Manager', 'Device', 'Interface', 'Node', 'Rpc')
            if None look inside the configuration file and raise error if not defined. 
        
        path (optional, str): an optional path to find the configuration inside the config file 
             'a.b.c' will go to cfg['a']['b']['c']
        default_type (optional, str): A default type if no type is defined in the configuration file
            If default_type is None and no type is found an error is raised

    Returns:
        obj : instanciatedpydevmgr object (Manager, Device, Node, Rpc, Interface)

    """
    Object, config = open_class(cfgfile, path=path, default_type=default_type, **kwargs)
    if key is None and isinstance(path, str): 
        _, name = ksplit(path)           
        key = kjoin(prefix, name)
    return Object(key, config=config)
        
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
    
    payload = _path_walk(payload, path)
   
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
    
    cls = _get_class_dict(payload)
    return cls, cls.parse_config(payload)

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
            kwargs['true_type'] = cls
            return cls.Config(**kwargs)
        if isinstance(__config__ , cls.Config):
            return __config__
        if isinstance(__config__, dict):
            d = {**__config__, **kwargs} 
            d['true_type'] = cls

            # if hasattr(cls.Config, "from_cfgdict"):
            #     return cls.Config.from_cfgdict(d)
            return cls.Config( **d )
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
            key: Optional[str]= None, 
            path: Optional[Union[str,int]] = None, 
            prefix: str = '', 
            **kwargs
        ) -> '_BaseObject':
        """ Create the object from a configuration file 
        
        Args:
            cfgfile (str): Path to the config file, shall be relative to one of the $CFGPATH or absolute
                     path
            key (str, Optional): key of the device, if not given this is built from the path suffix and
                    the optional prefix
           
            path (None, str, False)"" the hierarchique path where to find the config data inside the file 
                    for instance 'a.b.c' will loock at cfg['a']['b']['c'] from the loaded config file 
                    If "" the config file define the device configuration from its root 
                    If None the first item of the config file is taken 
            prefix (str, optional): add a prefix to the path name to build the device key. 
                    It is used only if key is None otherwhise ignored
        """
        
        allconf = load_config(cfgfile)
        allconf = _path_walk(allconf, path)
        
        allconf.update(**kwargs)
               
        if key is None and isinstance(path, str): 
            _, name = ksplit(path)           
            key = kjoin(prefix, name)
        
        return cls.from_cfgdict(allconf, key)
    
    @classmethod
    def from_cfgdict(cls, cfgdict, key: Optional[str] = None, *args, **kwargs):
        """ Open  """
        tpe = cls.Config.__fields__['type'].default 
        #config = cls.parse_config(cfgdict, type=tpe)
        config = cls.Config.from_cfgdict(cfgdict)               
        
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





                       
        
