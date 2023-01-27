from warnings import warn
from pydantic.class_validators import root_validator 
from valueparser import  ParserFactory

from .base import BaseObject

from typing import Dict, List, Callable,  Optional, Type, Any
from systemy import BaseSystem, FactoryDict, FactoryList


class Arg(BaseSystem):
    class Config:
        name: str
        parser: Optional[ParserFactory] = None
    
    def parse(self, value):
        if self.parser:
            return self.parser.parse(value)
        return value
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r} >"

def argc(name, parser=None):
    """ Helper to create an arg config 
    
    argc(name) -> Arg.Config( name=name, parser=None)
    argc(name, parser) -> Arg.Config( name=name, parser=parser)
    
    """
    return Arg.Config(name=name, parser=parser)


ArgsFactoryList = FactoryList[Arg.Config] 
KwargsFactoryDict = FactoryDict[str, Arg.Config] 

class BaseRpcConfig(BaseObject.Config):
    # ToDo remove arg_parsers and kwargs_parsers 
    # !!! These will be removed 
    arg_parsers: FactoryList[ParserFactory] = [] 
    kwarg_parsers: FactoryDict[str, ParserFactory] = {}
    # ################################################

    args: ArgsFactoryList = ArgsFactoryList()
    kwargs: KwargsFactoryDict = KwargsFactoryDict()
    
    @root_validator(pre=False)
    def _fix_legacy_parsers(cls, values):
        arg_parsers = values['arg_parsers']
        if not values.get('args', None)  and arg_parsers:
            warn( "arg_parser is deprecated, use the args argument", DeprecationWarning, stacklevel=2)

            values['args'] = ArgsFactoryList( 
                    [ Arg.Config(name=f"arg{i}", parser=arg_parser) for i,arg_parser in enumerate(arg_parsers)]
            )
        kwarg_parsers = values['kwarg_parsers']

        if not values.get('kwargs', None)  and kwarg_parsers:
            warn( "kwarg_parser is deprecated, use the kwargs kwargument", DeprecationWarning, stacklevel=2)

            values['kwargs'] = ArgsFactoryList( 
                    [ Arg.Config(name=f"kwarg{i}", parser=kwarg_parser) for i,kwarg_parser in kwarg_parsers.items()]
            )


        return values


class BaseCallCollector:
    """ The Read Collector shall collect all nodes having the same sid and read them in one call
    
    - __init__ : should not take any argument 
    - add : take three argument, the Rpc, list of args and dictionary of kwargs. Should add the rpc  in the 'call' queue 
    - call : takes a dictionary as arguement, read the nodes and feed the data according to node keys 
    
    The BaseReadCollector is just a dummy implementation where nodes are red one after the other     
    """
    def __init__(self):
        self._rpcs = []
    
    def add(self, rpc, args: List, kwargs: Dict) -> None:
        self._rpcs.append((rpc, args, kwargs))
        
    def call(self)-> None:        
        for rpc, args, kwargs in self._rpcs:
            rpc.rcall(*args, **kwargs)
                
class RpcError(RuntimeError):
    """ Raised when an rpc method is returning somethingelse than 0

        See rcall method of RpcNode
    """
    rpc_error = 0


class BaseRpc(BaseObject):
    
    Config = BaseRpcConfig
    Arg = Arg 

       
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] =None, 
           **kwargs
        ) -> None:  
        super().__init__(key, config=config, **kwargs)
        
        
          
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
        args = [ arg.parse(value) for value, arg in zip(args, self.args)]
        
        self_kwargs = self.kwargs 
        for k,v in kwargs.items():
            if k in self_kwargs:
                kwargs[k] = self_kwargs[k].parser.parse( v )

        return self.fcall(*args, **kwargs)
    
    def rcall(self, *args, **kwargs):
        """ Call the Rpc Method but raised an exception in case of an non-null error code is returned """
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
        

        
