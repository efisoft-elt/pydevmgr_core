from .node import BaseNode, NodesReader, NodesWriter
from .base import kjoin, BaseObject, new_key 
from .object_path import ObjPath
from .decorators import getter 

from typing import Union, List, Optional, Any, Dict, Callable
from pydantic import create_model
from inspect import signature , _empty


class NodeAliasConfig(BaseNode.Config):
    type: str = "Alias"
    # nodes: Optional[Union[List[Union[str, tuple, BaseNode.Config, BaseNode]], str, BaseNode.Config, BaseNode]] = None
    nodes: Optional[Any] = None 
     

class NodeAlias1Config(BaseNode.Config):
    type: str = "Alias1"
    # node: Optional[Union[str,tuple, BaseNode.Config, BaseNode]] = None
    node: Optional[Any] = None 

class BaseNodeAlias(BaseNode):
    
    @property
    def sid(self):
        """ sid of aliases must return None """ 
        return None
    
    def nodes(self):
        raise NotImplementedError('nodes')
    
    def get(self) -> Any:
        """ get the node alias value from server or from data dictionary if given """

        _n_data = {}
        nodes = list(self.nodes())
        NodesReader(nodes).read(_n_data)
        values = [_n_data[n] for n in nodes]
        
        return self.fget(*values)
    
    def set(self, value: Any) -> None:
        """ set the node alias value to server or to data dictionary if given """
        values = list(self.fset(value))
        nodes = list(self.nodes())
        if len(values)!=len(nodes):
            raise RuntimeError(f"fset method returned {len(values)} values while {len(self._nodes)} is on the node alias") 
        NodesWriter(dict(zip(nodes, values))).write()                        
            
    
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
            

class NodeAlias(BaseNodeAlias):
    """ NodeAlias mimic a real client Node. 
        
    The NodeAlias object does a little bit of computation to return a value with its `get()` method and 
    thanks to required input nodes.
     
    
    NodeAlias is an abstraction layer, it does not do anything complex but allows uniformity among ways to retrieve values. 
    
    NodeAlias object can be easely created with the @nodealias() decorator
    
    ..note::
    
        :class:`pydevmgr_core.NodeAlias` can accept one or several input node from the unique ``nodes`` argument. 
        To remove any embiguity NodeAlias1 is iddentical but use only one node as input from the ``node`` argument.  
            


    Args:
        key (str): Key of the node
        nodes (list, class:`BaseNode`): list of nodes necessary for the alias node. When the 
                     node alias is used in a :class:`pydevmgr_core.Downloader` object, the Downloader will automaticaly fetch 
                     those required nodes from server (or other node aliases).
                     
    Example: 
    
    Using a dummy node as imput (for illustration purpose).
    
    

    ::
        
        from pydevmgr_core.nodes import Value 
        from pydevmgr_core import NodeAlias
        position = Value('position', value=10.3)
        
        is_in_position = NodeAlias( nodes=[position])
        is_in_position.fget =  lambda pos: abs(pos-4.56)<0.1
        is_in_position.get()
        # False
        
    
    Using the nodealias decorator

    ::

        from pydevmgr_core.nodes import Value 
        from pydevmgr_core import NodeAlias
        position = Value('position', value=10.3)
        
        @nodealias_maker(position)
        def is_in_position(pos):
            return abs(pos-4.56)<0.1
 
    Derive the NodeAlias Class and add target position and precision  in configuration

    ::
 

        from pydevmgr_core.nodes import Value 
        from pydevmgr_core import NodeAlias
        position = Value('position', value=10.3)

        
        class InPosition(NodeAlias):
            class Config(NodeAlias.Config):
                target_position: float = 0.0 
                precision : float = 1.0 
            
            def fget(self, position):
                return abs( position - self.config.target_position) < self.config.precision 
        
        is_in_position = InPosition('is_in_position', nodes=[position],  target_position=4.56, precision=0.1)
        
        is_in_position.get()
        # False
        position.set(4.59)
        is_in_position.get()
        # True 
            
    NodeAlias can accept several nodes as input: 
    
    ::

        from pydevmgr_core.nodes import Value 
        from pydevmgr_core import NodeAlias
        
        class InsideCircle(NodeAlias):
            class Config(NodeAlias.Config):
                x: float = 0.0 
                y: float = 0.0
                radius: float = 1.0 
            
            def fget(self, x, y):
                return  ( (x-self.config.x)**2 + (y-self.config.y)**2 ) < self.config.radius**2
                
        position_x = Value('position_x', value=2.3)
        position_y = Value('position_y', value=1.4)
        is_in_target = InsideCircle( 'is_in_target', nodes=[position_x, position_y], x=2.0, y=1.0, radius=0.5 )
        is_in_target.get()
        # True


       
    .. seealso::  
        :func:`nodealias`
        :class:`NodeAlias1`            

    """
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
        if self._n_nodes_required is not None:
            if len(nodes)!=self._n_nodes_required:
                raise ValueError(f"{type(self)} needs {self._n_nodes_required} got {len(nodes)}")
        self._nodes = nodes
  
    def nodes(self):
        return self._nodes

      

    @classmethod
    def prop(cls,  name: str = None, nodes = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'NodeAlias: prop() method is deprecated, use instead the pydevmgr_core.decorators.getter to decorate the fget method from a node factory or the nodealias decorator', name, config_path, frozen_parameters)
        return getter( cls.Config(nodes=nodes, **kwargs) )  



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
        super().__init__(key, *args, **kwargs)    
        if node is None:            
            raise ValueError("the node pointer is empty, alias node cannot work without")    
                    
        self._node = node
    
    def nodes(self):
        yield self._node
  
     
    @classmethod
    def prop(cls,  name: str = None, node = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'NodeAlias: prop() method is deprecated, use instead the pydevmgr_core.decorators.getter to decorate the fget method from a node factory or the nodealias decorator', name, config_path, frozen_parameters)
        return getter( cls.Config(node=node, **kwargs) )     


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

   


    

