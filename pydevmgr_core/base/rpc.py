from warnings import warn 
from valueparser import BaseParser, ParserFactory

from .decorators import caller 
from .base import BaseObject

from typing import Dict, List, Callable,  Optional, Type, Any
from pydantic import create_model
from inspect import signature , _empty



class BaseRpcConfig(BaseObject.Config):
    
    arg_parsers: List[ParserFactory] = [] 
    kwarg_parsers: Dict[str, ParserFactory] = {}

class ArgParsers:
    """ responsable to parse a list of arguments """
    def __init__(self, parsers: List[BaseParser]):
        self._parsers = parsers
    
    def parse(self, args: List[Any]):
        modified_args = list(args)
        for i,(p,a) in enumerate(zip(self._parsers, args)):
            modified_args[i] = p.parse(a) 
        return modified_args

class DummyArgParser:
    """ dummy parser returning input """
    def parse(self, args):
        return args 

class KwargParsers:
    """ responsable to parse a dictionary of argument """
    def __init__(self, parsers: Dict[str, BaseParser]):
        self._parsers = parsers
    
    def parse(self, kwargs: Dict[str, Any]):
        modified_kwargs = dict(kwargs)
        
        for key,parser in self._parsers.items():
            if key in kwargs:
                modified_kwargs[key] = parser.parse( modified_kwargs[key] )
        
        return modified_kwargs
    
    
         


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



class BaseRpc(BaseObject):
    
    Config = BaseRpcConfig
    
    _arg_parsers = DummyArgParser()
    _kwarg_parsers = DummyArgParser()
    
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] =None, 
           **kwargs
        ) -> None:  
        super().__init__(key, config=config, **kwargs)
        
        
        if self.arg_parsers is not None:
            self._arg_parsers = ArgParsers( self.arg_parsers  )
        if self.kwarg_parsers is not None:
            self._kwarg_parsers = KwargParsers( self.kwarg_parsers )

  
    @property
    def sid(self):
        """ default id server is 0 
        
        The sid property shall be adujsted is the CallCollector
        """
        return 0
    
    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Rpc: prop() method is deprecated, use instead the pydevmgr_core.decorators.caller to decorate the fcall method from a rpc factory', name, config_path, frozen_parameters)
        return caller( cls.Config(**kwargs) )  
    
    
    def get_error_txt(self, rpc_error):
        """ Return Error text from an rpc_error code """
        return "Not Registered Error"
    
    def call_collector(self):
        """ Return a collector for method call """
        return BaseCallCollector()
                
    def call(self, *args, **kwargs):
        """ Call the method and return what return the server 
        
        this will mostly return an integer which shall be 0 if success
        
        .. seealso::
        
           :func:`BaseRpc.rcall` method
          
        """
        args   = self._arg_parsers.parse(args)
        kwargs = self._kwarg_parsers.parse(kwargs)
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
        EchoConfig(kind=<KINDS.RPC: 'Rpc'>, type='Echo', arg_parsers=None, kwarg_parsers=None, arg_parsers_config=[], kwarg_parsers_config={}, com=None, end='\n')
        
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
    




        
