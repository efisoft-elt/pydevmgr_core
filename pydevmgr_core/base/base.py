from os import path
from typing import Any, Tuple, Optional, List,  Union, Type, TypeVar, Iterator, get_type_hints
from pydantic import BaseModel, Extra,  create_model, root_validator
from pydantic.class_validators import root_validator

from pydevmgr_core.base.com import BaseCom


from .class_recorder import get_class, KINDS
from .model_var import StaticVar, NodeVar

from .defaults_var import _default_walk_set
import yaml
from .io import ioconfig, load_yaml, load_config, parse_file_name, PydevmgrLoader
import io as _io
import logging 
import weakref
from collections import UserDict, UserList 

log = logging.getLogger('pydevmgr')


ObjVar = TypeVar('ObjVar')




class BaseFactory(BaseModel):
    """ Factory is a pydantic model used to build pydevmgr object from the context of a parent object

    This is used when a configuration is not enough to build a pydevmgr object and more heavy transformation 
    on the input parameters has to be done. 
    
    Accept only one positional argument which is a config gile path to be loaded.
    If a file path is given no keyword argument are accepted 
    Otherwhise it works like a pydantic model, with keywords
    
    Example:
        
        F( k1=v1, k2=v2 ) 
        F( "relative/path/to/config.yml" )
    

    Methods:

        factory.build(parent) -> :class:`pydevmgr_core.BaseObject`
    """
    _name: Optional[str] = None
    class Config:
        extra = "forbid"
     
    def __init__(self, __yaml_file__ = None, **kwargs):
        if __yaml_file__:
            if kwargs:
                raise ValueError("Cannot mix root file and kwargs")
            kwargs = load_config(__yaml_file__)
        
        super().__init__( **kwargs)
       
    @classmethod
    def parse_obj(cls, obj):
        if isinstance(obj, str):
            return cls(obj)
        else:
            return super().parse_obj(obj)

    def build(self, parent: "BaseObject" = None, name: str = None) -> "BaseObject":
        raise NotImplementedError('build')
    
    
    def update(self, __d__=None, **kwargs):
        if __d__: 
            kwargs = dict(__d__, **kwargs)
        
        validate_assignment_state = self.__config__.validate_assignment
        try:
            self.__config__.validate_assignment = True 
            for key, value in kwargs.items():
                setattr( self, key, value)
        finally:
            self.__config__.validate_assignment = validate_assignment_state
        

    def __get__(self, parent, cls=None):
        if not isinstance(parent, BaseObject):
            return self


        if self._name is None:
            return self.build(parent, None)
        
        else:
            try:
                new_object = parent.__dict__[self._name]
            except KeyError:
                new_object = self.build(parent, self._name)
                
                parent.__dict__[self._name] = new_object  
            return new_object
        
    def __set_name__(self, owner, name):
        self.__dict__['_name'] = name

    @classmethod
    def parse_yaml(cls, payload: str):
        obj = load_yaml(payload)
        return cls.parse_obj(obj) 
    
class ObjectList(UserList):
    """ Explicitly contain a list of pydevmgr objects 

    An ObjectDict is typically returned by the build method of a :class:`pydevmgr_core.FactoryDict`
    
    ..Note::
        
        The item type is however not checked. This class is a away to explicitly tells the find engine 
        in pydevmgr that a list is owning pydevmgr objects 
    
    """
    def find(self, cls: Type, depth:int =0 ) -> Iterator:
        for obj in self:
            if isinstance(obj, cls):
                yield obj
            if  depth!=0 and isinstance(obj, (ObjectList,  ObjectDict, BaseParentObject)):
                 for sub in obj.find(cls, depth-1):
                    yield sub
    
    def build_all(self, depth:int =0):
        for obj in self:
            if isinstance(obj,(ObjectList,  ObjectDict, BaseParentObject)):
                obj.build_all(depth-1)
    

class ObjectDict(UserDict):
    """ Dictionary explicitly containing pydevmgr object as item 
    
    An ObjectDict is typically returned by the build method of a :class:`pydevmgr_core.FactoryDict`


    ..Note::
        
        The item type is however not checked. This class is a away to explicitly tells the pydevmgr engine 
        that the dictionary is owning pydevmgr objects.
    """
    def find(self, cls: Type, depth:int =0 ) -> Iterator:
        for obj in self.values():
            if isinstance(obj, cls):
                yield obj
            if  depth!=0 and isinstance(obj, (ObjectList, ObjectDict, BaseParentObject)):
                 for sub in obj.find(cls, depth-1):
                    yield sub
    
    def build_all(self, depth:int =0):
        for obj in self.values():
            if isinstance(obj, (ObjectList,  ObjectDict, BaseParentObject)):
                obj.build_all(depth-1)



class BaseConfig(BaseFactory):
    kind: KINDS = ""
    type: str = ""

    
    class Config: # this is the Config of BaseModel
        extra = Extra.forbid
        validate_assignment = True   
        use_enum_values = True 
    

    def _parent_class_ref(cls):
        # this is overwriten in __init_subclass__ of BaseObject by a weak reference of the parent class
        return None
    

    def _get_parent_class(self):
        """ Return the parent pydevmgr Object (Manager, Device, Interface, Node or Rpc ) for this configuration """
        p = self._parent_class_ref()
        if p is not None:
            return p
        return get_class(self.kind, self.type)

    def build(self, parent=None, name=None):
        if parent is None:
            return self._get_parent_class()( name, config=self )
        else:
            return self._get_parent_class().new(parent, name, config=self)
        
    @classmethod
    def from_cfgfile(cls, cfgfile, path: str = ''):
        """ Create the config object from a yaml config file 
        
        Args:
            cfgfile (str): Configuration file relative to one of $CFGPATH or absolute path 
            path (str, optional): path where to find the root configuration. if "" the config file 
                 contains the root. For instance 'a.b.c' will look at configuration in cfg['a']['b']['c']
        """
        config = load_config(cfgfile)
        if path is not None:
            config = path_walk_item(config, path)
        return cls.parse_obj(config)                    
    

def path_walk_item(d, path):
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


def path_walk_attr(obj, path):
    for p in (s for s in path.split('.') if s):
        obj = getattr(obj, p)
    return obj


def _path_name(d, path):
    if isinstance(path, int):
        if hasattr(d, "keys"):
            k = list(d.keys())[path]
            return k
        else:
            return None
    if isinstance(path, str):
        _, name = ksplit(path)
        return name 
    return None


def _get_class_dict( d, default_type: Optional[Union[str, Type]] = None):

    try:
        kind = d['kind']
    except KeyError:
        raise ValueError('"kind" attribute missing')
    
    
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
        pname (str, None) : The name of the object extracted from the path 
    """
    allconf = load_config(cfgfile)
    
    pname = _path_name(allconf, path)
    allconf = path_walk_item(allconf, path)
    
    allconf.update( kwargs )
    
    try:
        kind = allconf['kind']
    except KeyError:
        raise ValueError("Configuration has no 'kind' defined")

    tpe = allconf.get('type', default_type)
    if not tpe:
        raise ValueError(f"Cannot resolve {kind} type")
    Object = get_class(kind, tpe)
    config = Object.Config.parse_obj(allconf)
    return Object, config, pname 

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
    Object, config, pname = open_class(cfgfile, path=path, default_type=default_type, **kwargs)

    if key is None and pname:
        key = kjoin(prefix, pname)
    return Object(key, config=config)
        
class BaseData(BaseModel):
    # place holder for Data class 
    key: StaticVar[str] = ""

    
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

def path( keys: Union[str, list])-> Union[str, List[Union[str, tuple]]]:
    if isinstance(keys, str):
        l = keys.split(".")
        if len(l)<2:
            return keys
        return tuple(l)
    elif isinstance(keys, tuple):
        return keys
    elif hasattr( keys, '__iter__' ):
        return [path(k) for k in keys]
    return keys 
    #raise ValueError(f'expecting a string or an iterable on string got a {type(keys)}')

    


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
    """ A Property is basically calling a constructor with dynamical and static arguments """    
    def __init__(self, cls, constructor, name, *args, config=None, config_path=None, frozen_parameters=None,  **kwargs):
        
        self._cls = cls 
        self._constructor = constructor
        self._name = name         
        
        self._config = config 
        self._config_path = config_path
        if frozen_parameters is None:
            frozen_parameters = set()
        self._frozen_parameters = frozen_parameters
        self._args = args
        self._kwargs = kwargs

        for p in self._frozen_parameters:
            try:
                self._config.__dict__[p]
            except KeyError:
                ValueError(f"forzen parameter {p!r} does not exists in config")
        
    @property
    def congig(self):
        return self._config
            
    def _finalise(self, parent, obj):
        pass
    
    
    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name 


    def __get__(self, parent, clp=None):
        if parent is None:
            return self 
        # try to retrieve the node directly from the parent __dict__ where it should 
        # be cached. If no boj cached create one and save it/ 
        # if _name is the same than the attribute name in class, this should be called only ones
        if self._name is None:
            try:
                obj = parent.__dict__[self]
            except KeyError:
                name, obj = self.new(parent)     
                # store in parent with self
                parent.__dict__[self] = obj   
        else:
            try:
                obj = parent.__dict__[self._name]
            except KeyError:
                name, obj = self.new(parent)     
                # store in parent with the name 
                parent.__dict__[self._name] = obj   

        return obj
                
    def get_config(self, parent):
        """ return configuration from parent object """
        # this has to be implemented for each kinds
        if self._config_path:
            config = getattr( parent.config, self._config_path )
        elif self._name:
            try:
                config = getattr(parent.config, self._name)
            except AttributeError:
                config = self._config
        else:
            config = self._config
        if config is not self._config:
            if not isinstance( config, type(self._config) ):
                log.warning( f"The configuration Class missmatch in property {self._name!r} " )
            
            for p in self._frozen_parameters:
                if p in config.__fields_set__:
                    if getattr(config, p) != getattr(self._config, p):
                        raise ValueError("Cannot configure parameter {p!r}, frozen in property")
                setattr(config, p, getattr(self._config, p)) 
            _default_walk_set(self._config, config)
                
        return config    
            
                
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
        

class BaseObject:
    __all_cashed__ = False
    Config = BaseConfig
    Com = BaseCom
    Property = _BaseProperty    
    _config = None
    _com = None
    
    def __init_subclass__(cls, **kwargs) -> None:
         # if kwargs:
        subclass_defined_config = cls.Config
        if not issubclass( subclass_defined_config, BaseFactory):
            parent_config = None
            for subcl in cls.__mro__[1:]:
                try:
                    Tmp = getattr(subcl, "Config")
                except AttributeError:
                    continue
                else:
                    parent_config = Tmp
                    break 
            if not parent_config:
                raise ValueError("Cannot determine a Config class")
            
            type_hints = get_type_hints( subclass_defined_config)
            for name, val in subclass_defined_config.__dict__.items():
                if name.startswith("_"): continue 
                if name in kwargs:
                    continue 
                if name in type_hints:
                    kwargs[name] = (type_hints[name], val)
                else:
                    kwargs[name] = val 
            
            cls.Config = create_model(  cls.__name__+".Config",  __base__= parent_config, **kwargs)
        else:
            cls.Config = create_model(  cls.__name__+".Config",  __base__=cls.Config, **kwargs)
        cls.Config._parent_class_ref = weakref.ref(cls)


    def __init__(self, 
          key: Optional[str] = None,  
          config: Optional[Config] = None, 
          com: Optional[BaseCom] = None, 
          *,          
          localdata: Optional[dict] = None, 
          **kwargs 
        ) -> None:
       
        self._config = self.parse_config(config, **kwargs)    
        self._com = self.parse_com(com, self._config)
        if key is None: 
            key = new_key(self._config)
        
        self._key = key     
        self._localdata = localdata
        
    def __repr__(self):
        return "<{} key={!r}>".format(self.__class__.__name__, self._key)
    
    def __getattr__(self, attr):
        try:
            object.__getattribute__(self, attr)
        except AttributeError:
            return getattr(self._config, attr)
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        try:
            object.__getattribute__(self,  __name)
        except AttributeError:    
            try:
                getattr(self._config, __name)
            except AttributeError:
                object.__setattr__(self, __name, __value)
            else:
                raise AttributeError(f"{__name} is a config attribute and can be only changed in .config ")
        else:
            object.__setattr__(self, __name, __value)

    @classmethod
    def parse_config(cls, __config__=None, **kwargs):
        if __config__ is None:
            return cls.Config(**kwargs)
        if isinstance(__config__ , cls.Config):
            return __config__
        if isinstance(__config__, dict):
            d = {**__config__, **kwargs} 
            return cls.Config( **d )
        raise ValueError(f"got an unexpected object for config : {type(__config__)}")
    
    @classmethod
    def parse_com(cls, com, config):
        return cls.Com.new(com, config)
    

    @classmethod
    def new_args(cls, parent, name, config: Config) -> dict:
        """ build a dictionary of dynamical variables inerited from a parent """
        return dict( localdata = getattr(parent, "localdata", None) )
            
    @classmethod
    def new(cls, parent, name, config=None, **kwargs):
        """ a base constructor for BaseNode 
        
        parent must have the .key attribute 
        """        
        # here shall be implemented something to deal with config, it might be that config it comming
        # from the parent.config 
        config = cls.parse_config(config, **kwargs)
        if name is None:
            name = new_key(config)                                
        return cls(kjoin(parent.key, name), config=config, **cls.new_args(parent, name, config))
    
    @classmethod
    def prop(cls, name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        """ Return an object  property  to be defined in a class 
        
        Exemple:
           
           ::
                from pydevmgr_core import BaseDevice
                from pydevmgr_core.nodes import Static
                
                def MyDevice(BaseDevice):
                   ref_temperature = Static.prop(value=22.0)
                
                MyDevice().ref_temperature.get()   
        """
        # config = cls.Config.parse_obj(kwargs)
        config = cls.parse_config(kwargs)
        return cls.Property(cls, cls.new, name, config=config, config_path=config_path, frozen_parameters=frozen_parameters)
    
    @classmethod
    def from_cfgfile(cls, 
            cfgfile: str, 
            key: Optional[str]= None, 
            path: Optional[Union[str,int]] = None, 
            prefix: str = '', 
            **kwargs
        ) -> 'BaseObject':
        """ Create the object from a configuration file 
        
        Args:
            cfgfile (str): Path to the config file, shall be relative to one of the $CFGPATH or absolute
                     path
            key (str, Optional): key of the device, if not given this is built from the path suffix and
                    the optional prefix
           
            path (None, str, False)"" the hierarchique path where to find the config data inside the file 
                    for instance 'a.b.c' will loock at cfg['a']['b']['c'] from the loaded config file 
                    If "" the config file define the device configuration from its root 
                    If None the first item of the config file is taken. 
                    Note that the path can be defined directly inside the cfgfile file name
                    in the form ``path/to/myconfig.yml(a.b.c)` see :func:`load_config`

                                
            prefix (str, optional): add a prefix to the path name to build the device key. 
                    It is used only if key is None otherwhise ignored
        """
        
        allconf = load_config(cfgfile)
        allconf = path_walk_item(allconf, path)
        
        allconf.update(**kwargs)
               
        if key is None:
            if path and isinstance(path, str): 
                _, name = ksplit(path)           
                key = kjoin(prefix, name)
            else:
                # try with the path defined in file name 
                _, p = parse_file_name(cfgfile)
                if p:
                    key = p[-1]
                

        config = cls.Config.from_cfgfile( cfgfile, path )
        return cls(key = key, config=config, **kwargs)
            
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


class BaseParentObject(BaseObject):
    _all_cashed = False
    

   
    def find(self, cls: Type[BaseObject], depth: int = 0) -> Iterator:
        """ iterator on  children matching the given  class 
        
        ...note::
            
            The side effect of find is that all children will be built 

        Exemple::
            
            from pydevmgr_core import BaseNode
            list(   device.find( BaseNode, -1 ) ) # will return all nodes found in device and sub-devices, interface,
            etc...
        
        """
        if not self._all_cashed:
            self.build_all()
            self._all_cashed = True
        
        
        for  obj in self.__dict__.values():
            if isinstance(obj, cls):
                yield obj
            if depth!=0 and isinstance(obj, (ObjectList, ObjectDict, BaseParentObject)):
                for sub in obj.find(cls, depth-1):
                    yield sub
        
        
            
    def build_all(self, depth:int =0) -> None:
        """ Build all possible children objects 
        
        Every single children will be built inside the object and will be cashed inside the obj.__dict__
        
        """
        for sub in self.__class__.__mro__:
            for k,v in sub.__dict__.items():
                if isinstance(v, (_BaseProperty, BaseFactory)):
                    obj = getattr(self, k)
                    if depth!=0 and isinstance(obj, (ObjectList, ObjectDict, BaseParentObject)):
                        obj.build_all(depth-1)
        
        for k,c in self.config:
            if isinstance( c, (BaseFactory) ):
                obj = getattr( self, k)
                if depth!=0 and isinstance(obj, (ObjectList, ObjectDict, BaseParentObject)):
                        obj.build_all(depth-1)
                          
    
    def clear_all(self, cls=None) -> None:
        """ Remove all instances of cashed children objects 

        Args:
            cls (Type): A pydevmgr Class, default is the BaseObject 
            
        """
        if cls is None:
            cls = BaseObject
            
        for k,v in list(self.__dict__.items()):
            if isinstance( v, cls ):
                del self.__dict__[k]
        

    def __getattr__(self, attr):   
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            try:
                obj = getattr( self.config, attr  )
            except AttributeError:
                raise AttributeError(f"{attr!r}")
            if isinstance(obj, (BaseFactory)):
                new = obj.build( self, attr)
                self.__dict__[attr] = new
                return new 
            else:
                return obj

    def children(self, cls: Optional[BaseObject] = BaseObject) -> Iterator:
        """ iter on children attribute name 

        Args:
            cls: the class which shall match the object. By default it will be all pydevmgr objects
            (:class:`pydevmgr_core.BaseObject`)

        Example::
                
            >>> l = [getattr(manager, name) for name in  manager.children( BaseDevice )]
            # is equivalent to 
            >>> l = list (manager.find( BaseDevice, 0 ))

            
        """
        if not self._all_cashed:
            self.build_all()
            self._all_cashed = True
        for name, obj in self.__dict__.items():
            if isinstance(obj, cls):
                yield name  
    
    
    def create_data_class( self, children: Iterator[str],  Base = None ) -> Type[BaseData]:
        """ Create a new data class for the object according to a child name list 

        This is a quick and durty way to create a data class dynamicaly. To be used mostly 
        in a manager or device with dynamic children. 
        Manager, Device, Interface child will be build from their defined Data class 
        Nodes will be of ``Any`` type and filled with ``None`` as default. 
        
        """       
        data_obj = {}
        for name in children:
            obj = getattr(self, name)
            if hasattr( obj, "get"):
                data_obj[name] = (NodeVar[Any], None)
            else:
                data_obj[name] = (obj.Data, obj.Data())
        Base  = self.Data if Base is None else Base 
        return create_model( "Data_Of_"+self.key, __base__= Base, **data_obj  )

