from .node import BaseNode, NodesReader, NodesWriter
from .base import kjoin, BaseObject, new_key 
from .object_path import ObjPath
from .decorators import getter 

from typing import Union, List, Optional, Any, Dict, Callable
from pydantic import create_model
from inspect import signature , _empty, _ParameterKind, getattr_static


class NodeAliasConfig(BaseNode.Config):
    # nodes: Optional[Union[List[Union[str, tuple, BaseNode.Config, BaseNode]], str, BaseNode.Config, BaseNode]] = None
    nodes: Optional[Any] = None 
     

class NodeAlias1Config(BaseNode.Config):
    # node: Optional[Union[str,tuple, BaseNode.Config, BaseNode]] = None
    node: Optional[Any] = None 

class BaseNodeAlias(BaseNode):
    
    @property
    def sid(self):
        """ sid of aliases must return None """ 
        return None
    
    
    def get(self) -> Any:
        """ get the node alias value from server or from data dictionary if given """

        _n_data = {}
        nodes = list(self.nodes())
        NodesReader(nodes).read(_n_data)
        values = [_n_data[n] for n in nodes]
        
        return self.parse_output(self.fget(*values))
    
    def set(self, value: Any) -> None:
        """ set the node alias value to server or to data dictionary if given """
        values = list(self.fset(value))
        nodes = list(self.nodes())
        if len(values)!=len(nodes):
            raise RuntimeError(f"fset method returned {len(values)} values while {len(self._nodes)} is on the node alias") 
        NodesWriter(dict(zip(nodes, values))).write()                        
    
    def nodes(self):
        raise NotImplementedError('nodes')
          
    def fget(self, *args) -> Any:
        # Process all input value (taken from Nodes) and return a computed value 
        return args 
    
    def fset(self, value) -> Any:
        # Process one argument and return new values for the aliased Nodes 
        raise NotImplementedError('fset')    


class BaseNodeAlias1(BaseNodeAlias):
    def fget(self, value) -> Any:
        return value 
    def fset(self, value) -> Any:
        yield value 
            
class UNDEFINED:
    pass

def _guess_number_of_nodes(cls):
    meth = getattr_static(cls, 'fget')
    if isinstance( meth, (staticmethod, classmethod)):
        offset = 0
    else:
        offset = 1
    
    try:
        args = signature(cls.fget).parameters
    except ValueError:
        return None
    if not args:
        return 0 
    n = -offset
    for a in args.values():
        if a.kind == _ParameterKind.VAR_POSITIONAL:
            return None
        if a.kind == _ParameterKind.VAR_KEYWORD:
            continue
        if a.kind == _ParameterKind.KEYWORD_ONLY:
            continue
        n+=1
    return n
    

class NodeAlias(BaseNodeAlias):
    """ NodeAlias mimic a real client Node. """
    Config = NodeAliasConfig
    
    _n_nodes_required = None
    _nodes_is_scalar = False
    def __init__(self, 
          key: Optional[str] = None, 
          nodes: Union[List[BaseNode], BaseNode] = None,
          *args, **kwargs
         ):
        super().__init__(key, *args, **kwargs)
        if nodes is None:
            nodes = []
        
        elif isinstance(nodes, BaseNode):
            nodes = [nodes]
            self._nodes_is_scalar = True
            
        if isinstance(self._n_nodes_required, int) and self._n_nodes_required>-1:
            if len(nodes)!=self._n_nodes_required:
                raise ValueError(f"{type(self)} needs {self._n_nodes_required} got {len(nodes)}")
        self._nodes = nodes
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._n_nodes_required is None:
            cls._n_nodes_required = _guess_number_of_nodes(cls)
        elif cls.__mro__ and "fget" in cls.__mro__[0].__dict__ and cls.__mro__[0].__dict__.get("_n_nodes_required", None) is None:
            cls._n_nodes_required = _guess_number_of_nodes(cls)

    def nodes(self):
        return self._nodes

    
    @classmethod
    def new(cls, parent, name, config=None):
        """ a base constructor for a NodeAlias within a parent context  
        
        The requirement for the parent :
            - a .key attribute 
            - attribute of the given name in the list shall return a node
        """
        if config is None: 
            config = cls.Config()
        if config.nodes is None:
            nodes = []
        else:
            nodes = config.nodes
        # nodes = config.nodes                
        # handle the nodes now
        #if nodes is None:
        #    raise ValueError("The Node alias does not have origin node defined, e.i. config.nodes = None")
        if isinstance(nodes, str):
            nodes = [nodes]
        elif hasattr(nodes, "__call__"):
            nodes = nodes(parent)
                                
        parsed_nodes  = [ cls._parse_node(parent, n, config) for n in nodes ]
        
        return cls(kjoin(parent.key, name), parsed_nodes, config=config, com=parent.engine)
    
    @classmethod
    def _parse_node(cls, parent: BaseObject, in_node: Union[tuple,str,BaseNode], config: Config) -> 'NodeAlias':
        if isinstance(in_node, BaseNode):
            return in_node
        
        
        if isinstance(in_node, str):
            try:
                node = getattr(parent, in_node)
            except AttributeError:
                
                try:
                    node = ObjPath(in_node).resolve(parent)
                except Exception:
                    raise ValueError(f"The node named {in_node!r} cannot be resolved from its parent {parent}")
            if not isinstance(node, BaseNode):
                raise ValueError(f"Attribute {in_node!r} of parent is not node got a {node}")
            return node      
        
        if isinstance(in_node, tuple):
            cparent = parent
            for sn in in_node[:-1]:
                cparent = getattr(cparent, sn)
            
            name  = in_node[-1]
            try:
                node = getattr(cparent, name)
            except AttributeError:
                 raise ValueError(f"Attribute {name!r} does not exists in  parent {cparent}")
            else:
                if not isinstance(node, BaseNode):
                    raise ValueError(f"Attribute {in_node!r} of parent is not a node got a {type(node)}")
                return node

        
        raise ValueError('node shall be a parent attribute name, a tuple or a BaseNode got a {}'.format(type(in_node)))         
        
    def fget(self, *args) -> Any:
        """ Process all input value (taken from Nodes) and return a computed value """
        raise NotImplementedError("fget")

   

class NodeAlias1(BaseNodeAlias1):
    """ A Node Alias accepting one source node 
    
    By default this NodeAlias will return the source node. 
    One have to implement the fget and fset methods to custom behavior. 

    Example:
    
    ::
        
        from pydevmgr_core import NodeAlias1
        from pydevmgr_core.nodes import Value
             
        class Scaler(NodeAlias1, scale=(float, 1.0)):
            def fget(self, value):
                return value* self.config.scale
            def fset(self, value):
                yield value/self.config.scale 
    
        raw = Value('raw_value', value=10.2)
        scaled = Scaler('scaled_value', node = raw, scale=10)
        scaled.get()
        # -> 102
        scaled.set( 134)
        raw.get()
        # -> 13.4

    """
    Config = NodeAlias1Config
    
    def __init__(self, 
          key: Optional[str] = None, 
          node: Optional[BaseNode] = None,
          *args, **kwargs
         ):
        if node is None:            
            raise ValueError("the node pointer is empty, alias node cannot work without node")    
          
        super().__init__(key, *args, **kwargs)    
                  
        self._node = node
    
    def nodes(self):
        yield self._node
  

    @classmethod
    def new(cls, parent, name, config=None ):
        """ a base constructor for a NodeAlias within a parent context  
        
        The requirement for the parent :
            - a .key attribute 
            - attribute of the given name in the list shall return a node
        """
        if config is None:
            config = cls.Config()
        node = config.node
        if node is None:            
            node = config.node
        elif hasattr(node, "__call__"):
            node = node(parent)

        if node is None:
            raise ValueError("node origin pointer is not defined")                             
        parsed_node  = NodeAlias._parse_node(parent, node, config)    
        
        return cls(kjoin(parent.key, name), parsed_node, config=config, com=parent.engine)

    def fget(self,value) -> Any:
        """ Process the input retrieved value and return a new computed on """
        return value
    
    def fset(self, value) -> Any:
        """ Process the value intended to be set """
        yield value

   


    

