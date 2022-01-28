from ._class_recorder import get_rpc_class, KINDS
from ._core_base import (_BaseObject, _BaseProperty, 
                        ObjectIterator, ChildError, IOConfig, ksplit)
from ._core_com import BaseCom

from .. import io
from typing import Dict, List, Callable, Union , Optional, Any, Type
from pydantic import create_model, BaseModel
from ._core_parser import parser, AnyParserConfig
from inspect import signature , _empty

import weakref

class BaseRpcConfig(_BaseObject.Config):
    kind: KINDS = KINDS.RPC.value
    type: str = ""
    
    args_parser: Optional[List[Union[AnyParserConfig, List[Union[str, Callable]], str, Callable]]] = []
    kwargs_parser: Optional[Dict[str,Union[AnyParserConfig, List[Union[str, Callable]], str, Callable]]] = {}
    
    
    
    #args_parser: Optional[List[Union[str, Callable, Iterable]]] = None    
    #kwargs_parser: Optional[Dict[str,List[Union[str, Callable, Iterable]]]] = None
    #args_parser_config: List = []
    #kwargs_parser_config: Dict = {}
    
    class Config: # this is the Config of BaseModel
        extra = 'forbid'
        arbitrary_types_allowed = True
    
def parse_rpc_map(parentClass, map):        
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
                cls = parentClass.Rpc
            else:
                cls = get_rpc_class(type_)
            
            map[name] = cls.Config.parse_obj(conf)
        else:
            # TODO treat the node ?????
            map[name] = prop._cls.Config.parse_obj({**prop._config.dict(), **conf})
    
                                                
    for subcls in parentClass.__mro__:
        for name, obj in subcls.__dict__.items():
            if isinstance(obj, _BaseProperty):
                if issubclass(obj._cls, BaseRpc):
                    if not name in map:
                        map[name] = obj._config.copy(deep=True)

    
    
class BaseCallCollector:
    """ The Read Collector shall collect all nodes having the same sid and read them in one call
    
    - __init__ : should not take any argument 
    - add : take one argument, the Node. Should add node in the read queue 
    - read : takes a dictionary as arguement, read the nodes and feed the data according to node keys 
    
    The BaseReadCollector is just a dummy implementation where nodes are red one after the other     
    """
    def __init__(self):
        self._rpcs = []
    
    def add(self, rpc, args, kwargs):
        self._rpcs.append((rpc, args, kwargs))
        
    def call(self):        
        for rpc, args, kwargs in self._rpcs:
            rpc.rcall(*args, **kwargs)
                
class RpcError(RuntimeError):
    """ Raised when an rpc method is returning somethingelse than 0

        See rcall method of RpcNode
    """
    rpc_error = 0

class RpcProperty(_BaseProperty):    
    fcall = None
    
    def caller(self, func):
        """ decoraotr to define the fcall function """
        self.fcall = func
        return self # must return self
    
    def get_config(self, parent):
        try:
            sconf = parent.config.rpc_map[self._name]
        except (KeyError, AttributeError):
            return self._config.copy(deep=True)
        else:
            return sconf

    def _finalise(self, parent, rpc):
        if self.fcall:
            parent_wr = weakref.ref(parent)
            def fcall(*args, **kwargs):
                return self.fcall(parent_wr(), *args, **kwargs)
            rpc.fcall = fcall
    
    def __call__(self, func):
        """ The call is used has fcall decorator """
        self.fcall = func
        return self





class BaseRpc(_BaseObject):
    
    Config = BaseRpcConfig
    Property = RpcProperty
    
    _args_parser = None
    _kwargs_parser = None
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] =None, 
           **kwargs
        ) -> None:  
        super().__init__(key, config=config, **kwargs)
        
        if self.config.args_parser:
            _args_parser = []
            for i,p in enumerate(self.config.args_parser):                
                _args_parser.append(parser(p)) 
                self.config.args_parser[i] = _args_parser[i].config
            self._args_parser = _args_parser
        if self.config.kwargs_parser:
            _kwargs_parser = {}
            for k,p in self.config.kwargs_parser.items():
                _kwargs_parser[k] = parser(p)
                self.config.kwargs_parser[k] = _kwargs_parser[k].config    
            self._kwargs_parser  = _kwargs_parser


    @property
    def sid(self):
        """ default id server is 0 
        
        The sid property shall be adujsted is the CallCollector
        """
        return 0
    
    
    def get_error_txt(self, rpc_error):
        """ Return Error text from an rpc_error code """
        return "Not Registered Error"
    
    def call_collector(self):
        """ Return a collector for method call """
        return BaseCallCollector()
    
    def parse_args(self, args, kwargs):
        """ Modify in place a list of args and kwargs thans to the defined args_parser and kwargs_parser """
        if self._args_parser:
            for i,(p,a) in enumerate(zip(self._args_parser, args)):
                args[i] = p(a) 
        if self._kwargs_parser:
            for k,a in kwargs.items():
                try:
                    p = self._kwargs_parser[k]
                except KeyError:
                    pass
                else:
                    kwargs[k] = p(a)
                
    def call(self, *args, **kwargs):
        """ Call the method and return what return the server 
        
        this will mostly return an integer which shall be 0 if success
        
        .. seealso::
        
           :func:`BaseRpc.rcall` method
          
        """
        args = list(args)
        self.parse_args(args, kwargs)
        return self.fcall(*args, **kwargs)
    
    def rcall(self, *args, **kwargs):
        """ Call the Rpc Method but raised an exception in case of an error code is returned """
        e = self.get_error(self.call(*args, **kwargs))
        if e:
            raise e
    
    def get_error(self, rpc_return):
        if rpc_return:
            e = RpcError("RPC ({}): {}".format(rpc_return, self.get_error_txt(rpc_return)))
            e.rpc_error = rpc_return
            return e
    
    def fcall(self, *args, **kwargs):
        raise NotImplementedError('fcall')



class ComRpc(BaseRpc):
    """ a BaseRpc with a com attribute """
    class Config(BaseRpc.Config):
        type: str= "ComRpc"
        com: Optional[BaseCom.Config] = None
    
    def __init__(self, 
           key: Optional[str], 
           config: Optional[Config] =None, *, 
           com: Optional[Any] =None,  
           **kwargs
        ) -> None:
        self._com = com         
        super().__init__(key, config=config, **kwargs)

    @property
    def com(self):
        return self._com
    
    @classmethod
    def new_args(cls, parent, config):
        d = super().new_args(parent, config)
        d.upadte(com=parent.com)
        return d        
        
class _RpcListing:
    # This class shall be include in all parents with rpc as child  
    
    def _config_rpc_keys(self):
        return self.config.rpc_map.keys()
    
    def _config_rpc_constructor(self, name):
        try:
            rpcconf = self.config.rpc_map[name]
        except KeyError:
            raise ChildError(f"Unknown rpc {name}")
        return get_rpc_class(rpcconf.type).new    
    
    def _build_rpc(self, name):
        constructor = self._config_rpc_constructor(name)
        rpc = constructor(self, name, config=self.config.rpc_map[name])
        self.__dict__[name] = rpc 
        return rpc
    
    parse_rpc_map = classmethod(parse_rpc_map)     
    @classmethod
    def default_rpc_map(cls):
        return {}
    
    
    @property
    def rpcs(self) -> List[BaseRpc]:
        return ObjectIterator(self, self._build_rpc, self._config_rpc_keys())
    
    def get_rpc(self, name: str):
        try:
            #cached rpc
            rpc = self.__dict__[name]
        except KeyError:
            try:
                # static rpc, as property 
                rpc = object.__getattribute__(self, name)
            except AttributeError:
                rpc = self._build_rpc(name)                
            else:
                if not isinstance(rpc, BaseRpc):
                    raise ValueError(f"Unknown rpc {name}")          
        else:
            if not isinstance(rpc, BaseRpc):
                raise ValueError(f"Unknown rpc {name}")
        return rpc
    
    def add_rpc(self, name, rpc: Union[BaseRpc, BaseRpc.Config, dict]):
        """ Add a rpc
        
        This will also change the manager config.rpc_map 
        
        Args:
            name (str): The name (attribute) of the rpc
                
                ::
                
                    parent.add_rpc('move', move_rpc)
                    parent.move is move_rpc
            
            rpc (Node, Config , dict): A rpc object or a config to build the new rpc
        
        """    
        if isinstance(rpc, dict):
            type_ = rpc.get('type',None)
            if type_ is None:
                cls = self.Node
            else:
                cls = get_rpc_class(type_)
            if name is None:
                raise ValueError("name is missing")                                
            rpc = cls.new(self, name, **rpc)
        elif isinstance(rpc, BaseModel):
            if name is None:
                raise ValueError("name is missing") 
            rpc = cls.new(self, name, config=rpc)
            
        
        if name is None:
            _, name = ksplit(rpc.key)
        
        if name in self.config.rpc_map and self.config.rpc_map[name] != rpc.config:
            raise ValueError("Interface already exists inside the parent")
        elif name in self.__dict__:
            raise ValueError(f"attribute {name} is already taken")
        
        self.config.rpc_map[name] = rpc.config
        setattr(self, name, rpc)              

    def remove_rpc(self, name):
        """ Remove a rpc 
        
        This will remove also the configuration inside the config.rpc_map 
        An ValueError is raised if the rpc is not in the parent or if it has been defined 
        statisticaly on the class.
        
        Args:
            name (str) : the reference (the attribute) of the rpc
        """
        
        try:
            getattr(self.__class__, name)
        except AttributeError:
            if not name in self.config.rpc_map:
                raise ValueError("Unknown rpc {name!r}")
            
            del self.config.rpc_map[name]
            try:
                del self.__dict__[name]
            except KeyError:
                pass    
        else:
            raise ValueError("rpc {name!r} was defined inside the class")    
        
    
        

def rpcproperty(name, *args, **kwargs):
    """ A decorator for a quick rpc creation 
    
    This shall be implemented in a parent interface or any class 
    
    Args:
        cls (class, optional): default is :class:`BaseRpc` used to build the rpc  
        **kwargs: All other arguments necessary for the node construction
    """
    return BaseRpc.prop(name, *args, **kwargs)


def to_rpc_class(_func_: Callable = None, *, type: Optional[str] = None) -> Type[BaseRpc]:
    """ Create a Rpc Class from a function 
    
    This is a conveniant function to quickly create a Rpc Class. 
    As this is a lazy and durty implementation they are some naming convention to respect for the 
    function arguments. 
    The function can have the signature : 
    
    - `f(arg1, arg2, ..., key1=val1, key2=val2, ...)`
    
    Eventualy before the args 1 to 3 positional arguments can be named key, com and localdata 
    
    - `f(key, arg1, arg2, ..., key1=val1, key2=val2, ...)`
    - `f(key, com, arg1, arg2, ..., key1=val1, key2=val2, ...)`
    - `f(com, localdata, key, arg1, arg2, ..., key1=val1, key2=val2, ...)`
    - etc ...
    
    At call, com, localdata and key will be replaced by the corresponding Rpc instance attribute other
    positional argument are parsed to the function. 
    The keyowrd become parameters of the Config class 
    
    The to_rpc_class can be used as decorator or function 
    
    Example:
    
        >>> from pydevmgr_core import to_rpc_class
        >>> @to_rpc_class
        >>> def Echo(key, value, end: str = "\n"):
        >>>     print( key, "is called with value", value,  end=end)
      
        >>> Echo.Config()    
        EchoConfig(kind=<KINDS.RPC: 'Rpc'>, type='Echo', args_parser=None, kwargs_parser=None, args_parser_config=[], kwargs_parser_config={}, com=None, end='\n')
        
        >>> echo = Echo('echo!!', end="||\n")
        >>> echo.call(100)
        echo!! is called with value 100||
        >>> echo.config.end = "*********\n"
        >>> echo.call(100)
        echo!! is called with value 100*********
    
    The above class creation is equivalent of doing
    
    ::
    
       class Echo(BaseRpc):
            class Config(BaseRpc.Config):
                end: str = "\n"
            def fcall(self, value):
                print( self.key, "is called with value", value,  end=self.config.end)
    
    The penalty of the durty class creation is not so big: 1.5 to 2 times slower for the call 
    process only. Probably that what is inside the function will dominate the execution time anyway  
    """
    if _func_ is None:
        def rpc_func_decorator(func):
            return _rpc_func(func, type)
        return rpc_func_decorator
    else:
        return _rpc_func(_func_, type)
    
def _rpc_func(func, type_):
    if not hasattr(func, "__call__"):
        raise ValueError(f"{func} is not callable")
    
    try:    
        s = signature(func)
    except ValueError: # assume it is a builtin class with one argument 
        conf_args = {}
        obj_args = []
        
    else:
        
        conf_args = {}
        obj_args = []
        poasarg = False
        for a,p in s.parameters.items():
            if p.default == _empty:
                if a in ['com', 'localdata', 'key']:
                    if poasarg:
                        raise ValueError("Pos arguments must be after or one of 'com', 'localdata' or 'key'")
                    obj_args.append(a)
                else:
                    poasarg = True        
            else:                
                if p.annotation == _empty:
                    conf_args[a] = p.default 
                else:
                    conf_args[a] = (p.annotation,p.default)
                    
                    
    extras = {}
    if type_ is None:        
        if  "type" in conf_args:
            type_  = conf_args['type']            
        else:
            type_ = func.__name__
            extras['type'] = type_
    else:
        extras['type'] = type_
        
    Config = create_model(type_+"Config", **extras, **conf_args, __base__=BaseRpc.Config)
        
    if conf_args or obj_args: 
        conf_args_set = set(conf_args)        
        
        if obj_args:        
            def fcall_method(self, *args):
                c = self.config
                return func(*[getattr(self,__a__) for __a__ in obj_args], *args, **{a:getattr(c,a) for a in conf_args_set})
        else:
            def fcall_method(self, *args):   
                c = self.config         
                return func(*args, **{a:getattr(c,a) for a in conf_args_set})        
            
    else:
        def fcall_method(self, *args):
            return func(*args)
    try:
        doc = func.__doc__
    except AttributeError:
        doc = None           
    return type(type_+"Rpc", (BaseRpc,), {'Config':Config, 'fcall': fcall_method, '__doc__':doc})
    




        
