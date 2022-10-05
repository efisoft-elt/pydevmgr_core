from warnings import warn
from .class_recorder import get_class, KINDS, record_factory
from .base import (BaseObject, BaseData, ObjectFactory)
from .decorators import getter
from .parser_engine import  ParserFactory, NoneParserFactory 

import weakref
from inspect import signature , _empty

from pydantic import create_model,  validator
from typing import Dict, Any, Optional,  Callable,  Dict
from enum import Enum 



# used to force kind to be a node 
class NODEKIND(str, Enum):
    NODE = KINDS.NODE.value


@record_factory("Node")
class NodeFactory(ObjectFactory):
    """ A Factory for any type of node 
    
    The node is defined by the type string and must have been recorded before
    """
    kind: NODEKIND = NODEKIND.NODE

class BaseNodeConfig(BaseObject.Config):
    """ Config for a Node """
    kind: NODEKIND = NODEKIND.NODE
    type: str = ""
    parser: Optional[ParserFactory] = NoneParserFactory()
    description: str = ""
    unit: str = ""
    
        
class BaseReadCollector:
    """ Object used to collect nodes values from the same server in one roundtrip 
    
    It has two methods :
     .add(node) to add a node to the queue
     .read(data) to read nodes value inside a dictionary (data) 
    """
    ####
    #@ The Read Collector shall collect all nodes having the same sid and read them in one call
    #@ 
    #@ - __init__ : takes as many argument as necessary shall be build by the the BaseNode.read_collector method
    #@ - add : take one argument, the Node. Should add node in the read queue 
    #@ - read : takes a dictionary as arguement, read the nodes and feed the data dictionary where key  
    #@          is the node itself
    #@ The BaseReadCollector is just a dummy implementation where nodes are red one after the other     
    def __init__(self):
        self._nodes = set()
    def add(self, node):
        self._nodes.add(node)
    def read(self, data):
        for node in self._nodes:
            data[node] = node.get()

class BaseWriteCollector:
    """ Object used to write nodes values from the same server in one roundtrip 
    
    Its has two methods :
     .add(node, value) to add a node and its associated value to the queue
     .write() to write (upload) nodes values
    """
    ####
    #@ The Write Collector shall collect all nodes having the same sid, its value, and write them in one call
    #@ 
    #@ - __init__ : takes has many argument has necessary it shall be built by the BaseNode.write_collector method
    #@ - add : take two argument, the Node and its value attached. Should add node,value in the write queue 
    #@ - write  : takes no arguement, write the node/value 
    #@ 
    #@ The BaseWriteCollector is just a dummy implementation where nodes are written one after the other  
    
    def __init__(self):
        self._nodes = {}
    
    def add(self, node, value):
        self._nodes[node] = value
    
    def write(self):
        for node, val  in self._nodes.items():
            node.set(val)

class DictReadCollector:
    """ A collector to read from a dictionary instead of getting node from server 
    
    E.g. to be used as simulator
    """
    def __init__(self, data):
        self._data = data
        self._nodes = set()
        
    def add(self, node):
        self._nodes.add(node)
        
    def read(self, data):
        for node in self._nodes:
            data[node] = self._data[node.key]

class DictWriteCollector:
    """ A collector to write to a dictionary instead of setting node to server 
    
    E.g. to be used as simulator
    """
    def __init__(self, data):
        self._data = data
        self._nodes = {}
        
    def add(self, node, value):
        self._nodes[node] = value
        
    def write(self):
        for node, val  in self._nodes.items():
            self._data[node.key] = val


class BaseNode(BaseObject):
    """ This a base class defining the base methods for a node 
    
    The requirement for a Node is to have: 
        - a .key (str) attribute
        - a .sid (any hashable) attribute (iddenify an id to group nodes together for efficient reading and writting 
            in one server call). If sid is None the node is threated of an "alias Node".
            The only requirement for sid is that it should be hashable.
        - a .get(data=None) method 
        - a .set(value, data=None) method 
        - read_collector() : a constructor for a node collector for reading 
        - write_collector() : a constructor for a node collector for writting
    
    To implement from BaseNode one need to implement the .fget and .fset method (they are called by .get and .set)
    """
    Config = BaseNodeConfig


    class Data(BaseData):
        value: Any = None    
    _parser = None
    def __init__(self, 
           key: Optional[str] = None, 
           config: Optional[Config] = None, 
           com: Optional[Any] = None, 
           **kwargs
         ) -> None:
                                         
        super().__init__(key, config=config, com=com, **kwargs)
        if self._config.parser is not None:
            # !!! the parser builder can return None
            self._parser = self._config.parser.build(self) 
         
    @property
    def sid(self):
        """ default id server is 0 
        
        The sid property shall be adujsted according to read_collector and write_collector methods 
        """
        return 0
    
    @property
    def parser(self):
        return self._parser
    
    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Node: prop() method is deprecated, use instead the pydevmgr_core.decorators.getter to decorate the fget method from a node factory', name, config_path, frozen_parameters)
        return getter( cls.Config(**kwargs) )  
    
    def parse(self, value):
        """ Parse the value as it is done before being treated by the set method 
        
        The parsed value is the value received by the .fset(parsed_value) method 
        if self.parser is None :  `node.parse(value) is value`
        
        Args:
           value (any): value to be parsed
        
        Return:
            parsed_value (any): value parsed as it is done by the .set method 
        """
        if not self.parser:
            return value
        return self.parser.parse(value)
    
                    
    def read_collector(self) -> BaseReadCollector:
        """ return a collector of nodes for readding 
        
        This is used to collect all nodes with the same sid. 
        The result is done in one call per server when ever it is possible. 
        
        The returned object must have:
            a  ``.add(node)`` method 
            a  ``.read(data)`` method 
        
        The BaseReadCollector is however gettting the node value one by one. The method has to be 
        implemented for other Nodes
        """
        return BaseReadCollector()
    
    def write_collector(self) -> BaseWriteCollector:
        """ return a collector of nodes for writting
        
        This is used to collect all nodes with the same sid. All node could be written in one call
        on the server. 
        
        The returned object must have:
            a  ``.add(node, value)`` method 
            a  ``.write()`` method 
        
        The BaseWriteCollector is however setting the node value one by one. The method has to be 
        implemented for other Nodes
        """
        return BaseWriteCollector()
            
    def get(self) -> Any:
        """ get value of the data Node 
        
        If the optional data dictionary is given data[self] is return otherwise self.fget() is returned
        fget() will fetch the value from a distant server for instance (OPC-UA, Websocket, OLDB, etc ...)
        
        """
        return self.fget()
               
    def set(self, value, data=None):
        """ Set node value 
        
        If the optional data dictionary is given `data[self] = value`, otherwise  self.fset(value) is used 
        """
        value = self.parse(value)
        self.fset(value)

        if data is None:
            self.fset(value)
        else:
            data[self] = value
    
    ### ############################################
    #
    # To be implemented by the inerated class  
    #
     
    def fget(self):
        """ This is the function we need to implement to get real data """
        raise NotImplementedError('fget')
    
    def fset(self, value):
        """ This is the function we need to implement to set real data """
        raise NotImplementedError('fset')
                
    ### #############################################
    #  Optional reset will be mainly used on NodeAlias with some persistant data  
    def reset(self):
        pass



def node(key: Optional[str] =None):
    """ This is a node decorator 
    
    This allow to quickly embed any function in a node without having to subclass Node
    
    The build node will be readonly, for a more complex behavior please subclass a BaseNode
    
    Args:
        key (str): string key of the node
    
    Returns:
       func_setter: a decorator for the fget method  
       
    Example:
    
    A simulator of value:
    
    ::
        
        @node('temperature')
        def temperature():
            return np.random.random()*3 + 20
        
        temperature.get()
        
    Node returning the local float time in seconds 
    
    :: 
        
        @node('local_time')
        def local_time():
            return time.time()
    """
    node = BaseNode(key)
    def set_fget(func):
        node.fget = func
        if hasattr(func, "__func__"):
            node.__doc__= func.__func__.__doc__
        else:
            node.__doc__ = func.__doc__
        return node
    return set_fget


def setitem(obj,k,v):
    obj[k] = v

class NodesReader:
    def __init__(self, nodes=tuple()):
        self._input_nodes = nodes # need to save to remenber the order
        self._dispatch, self._aliases = {}, []
        for node in nodes:
            self.add(node) 
            
    def add(self, node):
        # if no _sid, this ia an alias or a standalone node and should be call 
        # at the end
        
        # None object are ignored 
        if node is None:
            return 
                
        if isinstance(node, (tuple, list, set)):
            for n in node:
                self.add(n)
         
        sid = node.sid 

        if sid is None:
            nodes = list(node.nodes())
            self._aliases.append( (node, nodes) )
            for n in nodes:            
                self.add(n)
            return         
        try:
            collection = self._dispatch[sid]
        except KeyError:
            collection = node.read_collector()
            self._dispatch[sid] = collection
        collection.add(node)
    
    def clear(self):
        self._dispatch.clear()
        self._aliases.clear()
    
    def read(self, data=None):
        """ read all node values 
        
        nodes are first grouped by sid and are red in one call is the server allows it 
        """
        # starts with the UA nodes 
        
        # :TODO: At some point, this should be asynchrone 
        for sid, collection in self._dispatch.items(): 
            collection.read(data)       
                
        # aliases are treated at the end, data should have all necessary real nodes for 
        # the alias 
        # We need to start from the last as Aliases at with lower index can depend 
        # of aliases with higher index
        aliases = self._aliases
        flags = [False]*len(aliases)
        for i, (alias, nodes) in reversed(list(enumerate(aliases))):
            if not flags[i]: 
                data[alias] = alias.fget( *(data[n] for n in nodes) )                    
                flags[i] = True

class NodesWriter:
    def __init__(self, node_values):
        
        self._dispatch = {}
        
        # start with aliases, returned values are set inside 
        # the node_values dictionary
        for node, value in node_values.items():
            if node.sid is None:
                for n,v in zip(node.nodes(), node.fset(value)):
                    node_values[n] = v 
        
        
        for node, value in node_values.items():
            if node.sid is not None:
                self.add(node, value)
    
    def clear(self):
        self._dispatch.clear()
        self._node_by_key.clear()
        
    def add(self, node, value):
        try:
            collection = self._dispatch[node.sid]
            
        except KeyError:
            collection = node.write_collector()
            self._dispatch[node.sid] = collection
        
        collection.add(node, value)
        
    def write(self) -> None:                
        # :TODO: At some point, this should be asynchrone 
        for collection in  self._dispatch.values():
            collection.write()


def new_node(type_, *args, **kwargs):
    """ Create a new node for a given type 
    
    ::
        new_node( tpe, *args, **kwargs) 

    Is just a short cut for

    ::
        get_class(KINDS.NODe, tpe)(*args, **kwargs)
    
    """
    cls = get_class(KINDS.NODE, type_)
    return cls(*args, **kwargs) 
        
        
def to_node_class(_func_: Callable =None, *, type: Optional[str] = None):
    if _func_ is None:
        def node_func_decorator(func):
            return _node_func(func, type)
        return node_func_decorator
    else:
        return _node_func(_func_, type)

def _node_func(func, type_):
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
        for a,p in s.parameters.items():
            if p.default == _empty:
                if a not in ['com', 'localdata', 'key']:
                    raise ValueError("All arguments must be keyword or one of 'com', 'localdata' or 'key'")
                obj_args.append(a)
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
                
    Config = create_model(type_+"Config", **extras, **conf_args, __base__= BaseNode.Config)
        
    if conf_args or obj_args: 
        conf_args_set = set(conf_args)        
                
        if obj_args:        
            def fget_method(self):
                c = self.config
                return func(*[getattr(self,__a__) for __a__ in obj_args], **{a:getattr(c,a) for a in conf_args_set})
        else:
            # def fget_method(self):
            #     return func(**self.config.dict(include=conf_args_set))  # this is slower       
            def fget_method(self):
                c = self.config
                return func(**{a:getattr(c,a) for a in conf_args_set})   
    else:
        def fget_method(self):
            return func()
    try:
        doc = func.__doc__
    except AttributeError:
        doc = None        
    return type(type_+"Node", (BaseNode,), {'Config':Config, 'fget': fget_method, '__doc__':doc})
    


