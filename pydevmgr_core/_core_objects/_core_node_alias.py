from ._core_node import BaseNode, NodesReader, NodesWriter
from ._core_base import kjoin, _BaseObject, new_key, path 
from typing import Union, List, Optional, Any, Dict, Callable
from pydantic import create_model, validator
from inspect import signature , _empty


class NodeAliasConfig(BaseNode.Config):
    type: str = "Alias"
    nodes: Optional[Union[List[Union[str, tuple]], str]] = None
    
 
class NodeAlias1Config(BaseNode.Config):
    type: str = "Alias1"
    node: Optional[Union[str,tuple]] = None
    


class NodeAliasProperty(BaseNode.Property):
    # redefine the node alias property to explicitly add the nodes argument
    def __init__(self, cls, constructor, name, nodes, *args, **kwargs):
        super().__init__( cls, constructor, name, *args, **kwargs)
        self._nodes = nodes
    
    def new(self, parent):
        config = self.get_config(parent)
        if self._name is None:
            name = new_key(config)
        else:
            name = self._name    
        obj = self._constructor(parent, name, self._nodes, *self._args, config=config, **self._kwargs)            
        self._finalise(parent, obj)
        return name, obj 
        
            
class NodeAlias(BaseNode):
    """ NodeAlias mimic a real client Node. 
        
    The NodeAlias object does a little bit of computation to return a value with its `get()` method and 
    thanks to required input nodes.
     
    The NodeAlias cannot be use as such without implementing a `fget` method. This can be done by 
    implementing the fget method on an inerated class or with the `nodealias` decorator. 
    
    NodeAlias is an abstraction layer, it does not do anything complex but allows uniformity among ways to retrieve values. 
    
    NodeAlias object can be easely created with the @nodealias() decorator
    
    Args:
        key (str): Key of the node
        nodes (list, class:`BaseNode`): list of nodes necessary for the alias node. When the 
                     node alias is used in a :class:`pydevmgr_core.Downloader` object, the Downloader will automaticaly fetch 
                     those required nodes from server (or other node aliases).
                     
    Example: 
    
    ::
    
        >>> is_inpos_for_test = NodeAlias('is_inpos_for_test', [mgr.motor1.stat.pos_actual])
        >>> is_inpos_for_test.fget = lambda pos: abs(pos-4.56)<0.01
        >>> is_inpos_for_test.get()
    
    :: 
    
        @nodealias("is_all_standstill", [mgr.motor1.stat.substate, mgr.motor2.stat.substate])
        def is_all_standstill(m1_substate, m2_substate):
            return m1_substate == Motor.SUBSTATE.OP_STANDSTILL and m2_substate == Motor.SUBSTATE.OP_STANDSTILL
    
        >>> is_all_standstill.get()
        True
        
        >>> downloader = Downloader( [is_all_standstill] )
        >>> downloader.download()        
        >>> downloader.get_data()
        {'fcs.motor1.substate': 100,
         'fcs.motor2.substate': 100,
         'is_all_standstill': False}
         
    In the exemple above one can see that the mgr.motor/1/2.stat.substate has been automatically added 
    to the nodes to be fetched from OPC-UA server(s). 
    
    Here is an exemple of customized NodeAlias, it return the mean and the max of a value, updated
    at each get :
    
    ::
    
        import numpy as np 
        
        class MinMaxNode(NodeAlias):
            min = +np.inf
            max = -np.inf
            
            def fget(self, pos):
                self.min = min(pos, self.min)
                self.max = max(pos, self.max)
                return ( self.min , self.max )
            
            def reset(self):
                self.min = +np.inf
                self.max = -np.inf
                
        mot1_minmax = MinMaxNode( "minmax",  [mgr.motor1.stat.pos_actual])
                
    .. seealso::  
        :func:`nodealias`
        :func:`nodealiasproperty`
        :class:`NodeAlias`            
    """
    Config = NodeAliasConfig
    Property = NodeAliasProperty
    
    _n_nodes_required = None
    _nodes_is_scalar = False
    def __init__(self, 
          key: Optional[str] = None, 
          nodes: Union[List[BaseNode], BaseNode] = None,
          config: Optional[Config] = None,
          **kwargs
         ):
         
        super().__init__(key, config=config, **kwargs)
        if nodes is None:
            nodes = []
        
        elif isinstance(nodes, BaseNode):
            nodes = [nodes]
            self._nodes_is_scalar = True
        if self._n_nodes_required is not None:
            if len(nodes)!=self._n_nodes_required:
                raise ValueError(f"{type(self)} needs {self._n_nodes_required} got {len(nodes)}")
        self._nodes = nodes
    
    @property
    def sid(self):
        """ sid of aliases must return None """ 
        return None
    
    @property
    def nodes(self):
        return self._nodes
    
    @classmethod
    def prop(cls, name: Optional[str] = None, nodes=None, **kwargs):
        nodes = [] if nodes is None else nodes
        #config = cls.Config.parse_obj(kwargs)  
        config = cls.parse_config(kwargs)
        return cls.Property(cls, cls.new, name, nodes, config=config)
                
    @classmethod
    def new(cls, parent, name, nodes=None, config=None, **kwargs):
        """ a base constructor for a NodeAlias within a parent context  
        
        The requirement for the parent :
            - a .key attribute 
            - attribute of the given name in the list shall return a node
        """
        config = cls.parse_config(config, **kwargs)
        if nodes is None:
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
                                
        parsed_nodes, node_names = zip(*(cls._parse_node(parent, n) for n in path(nodes)))
        
        return cls(kjoin(parent.key, name), parsed_nodes, config=config, localdata=parent.localdata, node_names=node_names)
    
    @classmethod
    def _parse_node(cls, parent: _BaseObject, in_node: Union[tuple,str,BaseNode]) -> 'NodeAlias':
        if isinstance(in_node, BaseNode):
            return in_node, in_node.key
        
        
        if isinstance(in_node, str):
            in_node, _, surname = in_node.partition(" as ")
            
            node = getattr(parent, in_node)
            if not isinstance(node, BaseNode):
                raise ValueError("Attribute {!r} of parent is not node got a {}".format(in_node, type(node)))
            return node, surname or in_node        
        
        if isinstance(in_node, tuple):
            cparent = parent
            for sn in in_node[:-1]:
                cparent = getattr(cparent, sn)
            
            name, _, surname = in_node[-1].partition(" as ")
            node = getattr(cparent, name)
            if not isinstance(node, BaseNode):
                raise ValueError("Attribute {!r} of parent is not a node got a {}".format(in_node , type(node)))
            return node, name or surname
            
        raise ValueError('node shall be a parent attribute name, a tuple or a BaseNode got a {}'.format(type(in_node)))         
        
    def get(self, data: Optional[Dict] =None) -> Any:
        """ get the node alias value from server or from data dictionary if given """
        if data is None:
            _n_data = {}
            NodesReader(self._nodes).read(_n_data)
            values = [_n_data[n] for n in self._nodes]
            #values = [n.get() for n in self._nodes]
        else:
            values = [data[n] for n in self._nodes]
        return self.fget(*values)
    
    def set(self, value: Any, data: Optional[Dict] =None) -> None:
        """ set the node alias value to server or to data dictionary if given """
        values = self.fset(value)
        if data is None:
            NodesWriter(dict(zip(self._nodes, values))).write()                        
            #for n,v in zip(self._nodes, values):
            #    n.set(v)
        else:
            for n,v in zip(self._nodes, values):
                data[n] = v        
    
    def fget(self, *args) -> Any:
        """ This is the function we need to implement to get real data 
        
        The number of argument must match the number of nodes
        """
        raise NotImplementedError('fget')
    
    def fset(self, value) -> None:
        """ This is the function we need to implement to set real data
         
        The number of returned value must match the number of nodes 
        """
        raise NotImplementedError('fset')    




class NodeAlias1(BaseNode):
    Config = NodeAlias1Config
    Property = NodeAliasProperty
    
    def __init__(self, 
          key: Optional[str] = None, 
          node: Optional[BaseNode] = None,
          config: Optional[Config] = None, 
          localdata: Optional[dict] = None, 
          node_name: Optional[str] = None, 
          **kwargs
         ):        
        super().__init__(key, config=config, localdata=localdata, **kwargs)    
        if node is None:            
            raise ValueError("the node pointer is empty, alias node cannot work without")    
                    
        self._node = node
        self._node_name = node_name
    
    @property
    def sid(self):
        """ sid of aliases must return None """ 
        return None
    
    @property
    def node(self):
        return self._node
    
    # nodes property is mendatory for the NodeReader 
    @property
    def nodes(self):
        return [self._node]
    
    @classmethod
    def prop(cls, 
          name: Optional[str] = None, 
          node: Union[BaseNode,str] = None,  
          **kwargs
        ) -> NodeAliasProperty:
        # config = cls.Config.parse_obj(kwargs)
        config = cls.parse_config(kwargs)
        return cls.Property(cls, cls.new, name, node, config=config)
    
    @classmethod
    def new(cls, parent, name, node=None,  config=None, **kwargs):
        """ a base constructor for a NodeAlias within a parent context  
        
        The requirement for the parent :
            - a .key attribute 
            - attribute of the given name in the list shall return a node
        """
        config = cls.parse_config(config, **kwargs)
        if node is None:            
            node = config.node 
        if node is None:
            raise ValueError("node origin pointer is not defined")                             
        parsed_node, node_name = NodeAlias._parse_node(parent, path(node))    
        
        return cls(kjoin(parent.key, name), parsed_node, config=config, localdata=parent.localdata, node_name=node_name)
    
    
    def get(self, data: Optional[Dict] =None) -> Any:
        """ get the node alias value from server or from data dictionary if given """
        if data is None:
            _n_data = {}
            NodesReader([self._node]).read(_n_data)
            value = _n_data[self._node]
        else:
            value = data[self._node]
        return self.fget(value)    
        
    def set(self, value: Any, data: Optional[Dict] =None) -> None:
        """ set the node alias value to server or to data dictionary if given """
        value = self.fset(value)
        if data is None:
            NodesWriter({self._node:value}).write()                        
            #for n,v in zip(self._nodes, values):
            #    n.set(v)
        else:
            data[self._node] = value
    
    def fget(self,value) -> Any:
        """ This is the function we need to implement to get real data 
        
        One argument for NodeAlias1
        """
        raise NotImplementedError('fget')
    
    def fset(self, value) -> None:
        """ This is the function we need to implement to set real data
         
        Must return one single value for NodeAlias1
        """
        raise NotImplementedError('fset')    


def nodealiasproperty(name, nodes, *args, **kwargs):
    """ A decorator for a quick alias node creation 
    
    This shall be implemented in a parent interface or any class with the ``get_node`` method
    
    Args:
        name (str) : name of the node. The key of the node will be parent_key.name
        nodes (iterable): List of a mix of node or string coresponding to the parent attribute pointing
                          to a node.  
        \*args, \**kwargs: All other arguments necessary for the node construction this is only used 
                         if an laternative cls is given 
    """
    return NodeAlias.prop(name, nodes, *args, **kwargs)


def nodealias1property(name, node, *args, **kwargs):
    """ A decorator for a quick alias node creation 
    
    This shall be implemented in a parent interface or any class with the ``get_node`` method
    
    Args:
        name (str) : name of the node. The key of the node will be parent_key.name
        node (:class:`BaseNode`, str): Either a node or a string coresponding to the parent attribute 
                pointing to a node.  
        \*args, \**kwargs: All other arguments necessary for the node construction 
    """
    return NodeAlias1.prop(name, node, *args, **kwargs)



def nodealias(key: Optional[str] =None, nodes: Optional[list] = None):
    """ This is a node alias decorator 
    
    This allow to quickly embed any function in a node without having to subclass the Alias Node
    
    The build node will be readonly, for a more complex behavior please subclass a NodeAlias
    
    Args:
        key (str): string key of the node
        nodes (lst): list of nodes 
        
    Returns:
       func_setter: a decorator for the fget method  
       
    Example:
    
    A simulator of value:
    
    ::
        
        # To be replaced by real stuff of course
        @node('temperature')
        def temperature():
            return np.random.random()*3 + 20
        @node('motor_pos')
        def motor_pos():
            return np.random.random()*100
        
        # the nodealias focus is computed from temperature and motor position 
        @nodealias('focus', [temperature, motor_pos]):
        def focus(temp, pos):
            return pos+ 0.45*temp + 23.
            
    In the example above when doing `focus.get()` it will automaticaly fetch the `temperature` and
    `motor_pos` nodes.  
        
    """
    node = NodeAlias(key,nodes)
    def set_fget(func):
        node.fget = func
        if hasattr(func, "__func__"):
            node.__doc__= func.__func__.__doc__
        else:
            node.__doc__ = func.__doc__
        return node
    return set_fget



def nodealias1(key: Optional[str] = None, node: Optional[BaseNode] = None) -> Callable:
    """ This is a node alias decorator 
    
    This allow to quickly embed any function in a node without having to subclass the Alias Node
    This is the counterpart of :func:`nodealias` except that it explicitely accept only one node
    as input instead of severals
    
    The build node will be readonly, for a more complex behavior please subclass a NodeAlias
    
    Args:
        key (str, optional): string key of the node
        node (:class:`BaseNode`): input node. This is not optional and shall be defined 
                                  It is however after key for historical reason 
        
    Returns:
       func_setter: a decorator for the fget method  
       
    Example:
    
    A simulator of value:
    
    ::
        
        @node('temperature_volt')
        def temperature_volt():
            return np.random.random()*3 + 20
        
        @nodealias1('temperature_celcius', temperature_volt):
        def temperature_celcius(temp_volt):
            return temp_volt*12.3 + 2.3
            
    """
    node = NodeAlias1(key,node)
    def set_fget(func):
        node.fget = func
        if hasattr(func, "__func__"):
            node.__doc__= func.__func__.__doc__
        else:
            node.__doc__ = func.__doc__
        return node
    return set_fget

def to_nodealias_class(_func_: Callable =None, *, type: Optional[str] = None):
    if _func_ is None:
        def node_func_decorator(func):
            return _nodealias_func(func, type)
        return node_func_decorator
    else:
        return _nodealias_func(_func_, type)
    
    
def _nodealias_func(func, type_):
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
        poasarg = 0
        for a,p in s.parameters.items():
            if p.default == _empty:
                if a in ['com', 'localdata', 'key', 'nodes']:
                    if poasarg:
                        raise ValueError("Pos arguments must be after or one of 'com', 'localdata' or 'key'")
                    obj_args.append(a)
                else:
                    poasarg += 1        
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
        
          
                
    Config = create_model(type_+"Config", **extras, **conf_args, __base__=NodeAlias.Config)
        
    if conf_args or obj_args: 
        conf_args_set = set(conf_args)        
                
        if obj_args:        
            def fget_method(self, *args):
                c = self.config
                return func(*[getattr(self,__a__) for __a__ in obj_args], *args, **{a:getattr(c,a) for a in conf_args_set})
        else:
            def fget_method(self, *args): 
                c = self.config           
                return func(*args, **{a:getattr(c,a) for a in conf_args_set})        
            
    else:
        def fget_method(self, *args):
            return func(*args)
    try:
        doc = func.__doc__
    except AttributeError:
        doc = None
                   
    return type(type_+"NodeAlias", 
                (NodeAlias,), 
                {'Config':Config, 'fget': fget_method, '__doc__':doc, '_n_nodes_required': poasarg}
               )
    



    

