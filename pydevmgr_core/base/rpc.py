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
        

        
