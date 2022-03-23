from ._core_objects import  BaseNode, NodeAlias, NodeAlias1, record_class

from collections import deque
import time
from  datetime import datetime, timedelta
from typing import Union, List, Dict, Optional
from pydantic import validator
from enum import Enum
from py_expression_eval import Parser
from dataclasses import dataclass
import math 


_eval_parser = Parser()


__all__ = [
"UnixTimeNode",
"LocalTimeNode",
"LocalUtcNode", 
"DequeNode", 
"DequeNode1",
"local_utc", 
"local_utc2", 
"local_time",
"AllTrue", 
"AllFalse", 
"AnyTrue", 
"AnyFalse",
"NegNode", 
"InsideIntervalNode", 
"InsideCircleNode", 
"PosNameNode", 
"FormulaNode", 
"FormulaNode1",
"PolynomNode1",
"StatisticNode", 
"CounterNode", 
"FormatNode", 
"SumNode", 
"MeanNode", 
"MinNode", 
"MaxNode"
]

@record_class
class UnixTimeNode(BaseNode):
    """ A basic node returning the float local time  
    
    Args:
        key (optional, str): node key
        delta (optional, float): time shift in seconds 
    
    """
    class Config(BaseNode.Config):
        type = "UnixTime"
        delta: float = 0.0
    
    def __init__(self, key: str = 'local_unix_time', config=None, **kwargs):
        super().__init__(key, config=config, **kwargs)
        
    def fget(self) -> float:
        return time.time()+self.config.delta 

@record_class
class LocalTimeNode(BaseNode):
    """ A basic node returning the float local time  
    
    Args:
        key (optional, str): node key
        delta (optional, float): time shift in seconds 
        
    Properties:
        _delta : the _delta timeshift in second 
    """
    class Config(BaseNode.Config):
        type = "LocalTime"
        delta: float = 0.0 # delta in seconds 
        
    def __init__(self, key: str = 'local_time', config=None, **kwargs):
        super().__init__(key, config=config, **kwargs)
    
    def fget(self) -> float:
        return datetime.now()+timedelta(seconds=self.config.delta)
        

local_time = LocalTimeNode('local_time')

@record_class
class LocalUtcNode(BaseNode):
    """ A basic node returning the local UTC as string 
    
    Args:
        key (str, optional): node key
        delta (float, optional): time shift in seconds 
        format (str, optional): Returned format, default is iso 8601 '%Y-%m-%dT%H:%M:%S.%f%z'
    Properties:
        _delta : the _delta timeshift in second 
    """
    class Config(BaseNode.Config):
        type = "LocalUtc"
        delta: float = 0.0
        format: str = '%Y-%m-%dT%H:%M:%S.%f%z'
        
    def __init__(self, key : str ='local_utc', config=None, **kwargs):
        super().__init__(key, config=config, **kwargs)
                
    def fget(self) -> str:
        tc = datetime.utcnow()+timedelta(seconds=self.config.delta)   
        return tc.strftime(self.config.format)
        
##
# Add an instance to the local_utc 
local_utc  = LocalUtcNode('local_utc')
local_utc2 = LocalUtcNode('local_utc', format='%Y-%m-%d-%H:%M:%S.%f%z')


@record_class
class DequeNode(NodeAlias):
    """ This is an :class:`NodeAlias` returning at each get a :class:`collections.deque` 
    
    Specially handy for live plot and scopes
    
    Args:
       key (string): alias node keyword 
       nodes (list of :class:`UaNode`,:class:`NodeAlias`): 
              List of nodes to get()  
       maxlen (int): maximum len of the dequeu object  
    
    Example:
        
    In this example the first motor is moving while the second standstill at 0.0
         
    ::
    
        >>> from pydevmgr_core import local_time
        >>> time = UnixTimeNode('time') 
        >>> nodes = [time, mgr.motor1.stat.pos_actual, mgr.motor2.stat.pos_actual]
        >>> f = DequeNode( "mot_poses", nodes, 20)
        >>> f.get()
        deque([(1604931613.136023, 96.44508185106795, 0.0)])
        >>> f.get()
        deque([(1604931613.136023, 96.44508185106795, 0.0),
        (1604931614.258859, 95.32508185106808, 0.0)])
        >>> f.get()
        deque([(1604931613.136023, 96.44508185106795, 0.0),
        (1604931614.258859, 95.32508185106808, 0.0),
        (1604931615.451603, 94.13508185106821, 0.0)])
        >>> etc ....
        
    """
    class Config(NodeAlias.Config):
        type = "Deque"
        maxlen: int = 10000
        trigger_index: Optional[int] = None
    
    def __init__(self, 
          key: Optional[str] = None, 
          nodes: Optional[Union[BaseNode,List[BaseNode]]] = None, 
          config: Optional[Config] = None,
          **kwargs
        ) -> None: 
        
        if nodes is None:
            raise ValueError("nodes cannot be None")    
        super().__init__(key, nodes, config, **kwargs)        
        
        self._data = deque([], self._config.maxlen)
        self._scalar = not hasattr(nodes, "__iter__")
                
        
    @property
    def data(self):
        return self._data 
    
    @property
    def columns(self):
        return [n.key for n in self.nodes]
    
        
    def fget(self, *values): 
        if self.config.trigger_index is not None and not values[self.config.trigger_index]:
            return self._data      
        
        if self._scalar:
            self._data.append(values[0])
        else:
            self._data.append(values)
        return self._data
    
    def reset(self, maxlen=None):
        if maxlen is not None:
            self.config.maxlen = maxlen
                
        if self._maxlen != self._config.maxlen:             
            # maxlen has been changed 
            self._maxlen = self._config.maxlen        
            self._data = deque([], self._config.maxlen)
        else:
            self._data.clear()
        
@record_class
class DequeNode1(NodeAlias1):
    """ This is an :class:`NodeAlias1` returning at each get a :class:`collections.deque` 
    
    Specially handy for live plot and scopes
    
    Args:
       key (string): alias node keyword 
       node  ( :class:`UaNode`,:class:`NodeAlias`): 
              
       maxlen (int): maximum len of the dequeu object  
    
    .. seealso::
       :class:`DequeNode` 
        
    """
    class Config(NodeAlias.Config):
        type = "Deque1"
        maxlen: int = 10000        
    
    def __init__(self, 
          key: Optional[str] = None, 
          node: Optional[Union[BaseNode,List[BaseNode]]] = None, 
          config: Optional[Config] = None,
          **kwargs
        ) -> None: 
        
        if node is None:
            raise ValueError("node cannot be None")    
        super().__init__(key, node, config, **kwargs)
        self._maxlen = self._config.maxlen        
        self._data = deque([], self._config.maxlen)                        
        
    @property
    def data(self):
        return self._data 
        
    def fget(self, value):         
        self._data.append(value)
        return self._data
    
    def reset(self, maxlen=None):
        if maxlen is not None:
            self.config.maxlen = maxlen
                
        if self._maxlen != self._config.maxlen:             
            # maxlen has been changed 
            self._maxlen = self._config.maxlen        
            self._data = deque([], self._config.maxlen)
        else:
            self._data.clear()


@record_class
class AllTrue(NodeAlias):
    class Config(NodeAlias.Config):
        type = "AllTrue"
    def fget(*nodes):
        return all(nodes)

@record_class
class AnyTrue(NodeAlias):
    class Config(NodeAlias.Config):
        type = "AnyTrue"
    def fget(*nodes):
        return any(nodes)
        
@record_class        
class AllFalse(NodeAlias):
    class Config(NodeAlias.Config):
        type = "AllFalse"
    def fget(*nodes):
        return not any(nodes)

@record_class
class AnyFalse(NodeAlias):
    class Config(NodeAlias.Config):
        type = "AnyFalse"
    def fget(*nodes):
        return not all(nodes)

@record_class
class NegNode(NodeAlias1):
    """ Return the negative of the aliased node """
    class Config(NodeAlias1.Config):
        type = "NegNode"
    def fget(self, value):
        return not value 

@record_class
class CounterNode(BaseNode):
    """ A simple counter node at each get the counter is increased and returned 
    
    Args:
        start (optional, int): start number 
        
    Example:
    
    ::
    
       >>> c = CounterNode()
       >>> c.get()
       1
       >>> c.get()
       2
       >>> c.reset()
       >>> c.get()
       1
    """
    class Config(BaseNode.Config):
        type: str = "Counter"
        start: int  = 0
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
    
    def reset(self):
        self._counter = self.config.start
    
    def fget(self):
        self._counter += 1
        return self._counter 
        
@record_class
class InsideIntervalNode(NodeAlias1):
    """ Bool Node alias to check if a value is inside a given interval 
    
    Args:
        key (str):  node key
        node (:class:`BaseNode`): node returning a float 
        min (float, optional): min value of the interval 
        max (float, optional): max value of the interval
    """
    class Config(NodeAlias1.Config):
        type = "InsideInterval"
        min : Optional[float] = None
        max : Optional[float] = None
            
    def fget(self, value):
        c = self.config
        if c.min is not None and value<c.min:
            return False
        if c.max is not None and value>c.max:
            return False
        return True    
        
@record_class
class InsideCircleNode(NodeAlias):
    """ Bool Node alias to check if a 2d position is inside a circle 
    
    Args:
        key (str): node key
        nodes (list of :class:`BaseNode`): two nodes returning x and y coordinates 
        x0, y0 (float): circle origin  default is (0.0, 0.0)
        r (float): circle radius (default is 1.0)
    
    """
    class Config(NodeAlias.Config):
        type = "InsideCircle"
        x0 : float = 0.0
        y0 : float = 0.0 
        r  : float = 1.0
            
    _n_nodes_required = 2    
    
    def fget(self, x, y):
        c = self.config
        return ((x-c.x0)**2 + (y-c.y0)**2) < (c.r*c.r)        
        

@record_class    
class PosNameNode(NodeAlias1):
    """ Node alias returning a position name thanks to a list of position and a tolerance 
    
    Args:
        key (str):  node key 
        node (:class:`BaseNode`)
        poses (dict):  name/position pairs
        tol (float): tolerence for each poses
        unknown (str, optional): string for unknown position default is ""
        
    Example:
       
    :: 
       
       PosNameNode('pos_name', motor1.stat.pos_actual, {'FREE':0.0, ''})
    """
    class Config(NodeAlias1.Config):
        type = "PosName"
        poses: Dict[str,float] = None
        tol: float = 0.0 
        unknown: str = ""
        
    def fget(self, value: float) -> str:
        c = self.config
        for name, pos in c.poses.items():
            if abs(pos-value)<c.tol:
                return name
        return c.unknown
         
     
@record_class    
class FormulaNode(NodeAlias):
    class Config(NodeAlias.Config):
        type: str = "Formula"
        formula : str = "-99.99"
        varnames: Optional[Union[List[str],str]] = None  
    
    def __init__(self, *args, **kwargs):                            
        super().__init__(*args, **kwargs)
        if isinstance(self.config.varnames, str):
            varnames = [self.config.varnames]
        else:
            varnames = self.config.varnames
        if varnames is  None:
            if len(self.nodes)==1:
                varnames = ('x',)
            else:
                varnames = tuple( 'x'+str(i+1) for i in range(len(self.nodes)) )
        elif len(varnames)!=len(self.nodes):
            raise ValueError( f"Got {len(self.nodes)} nodes but configured varnames has size {len(self.config.varnames)}")
                    
        self._parser = _eval_parser.parse(self.config.formula)
        self._inputs = {'nan': math.nan}
        
        self._varnames = varnames
            
                
    def fget(self, *values):   
        v = {k:x for k,x in zip(self._varnames, values)}
        return self._parser.evaluate(v)


@record_class    
class FormulaNode1(NodeAlias1):
    class Config(NodeAlias1.Config):
        type: str = "Formula1"
        formula : str = "-99.99"
        varname: str = 'x' 
    
    def __init__(self, *args, **kwargs):                            
        super().__init__(*args, **kwargs)
                
        self._parser = _eval_parser.parse(self.config.formula)
        self._inputs = {'nan': math.nan}
        
        self._varname = self.config.varname
                            
    def fget(self, value):          
        return self._parser.evaluate({self._varname:value})


@record_class
class PolynomNode1(NodeAlias1):
    """ Apply a polynome 

    Config:
        polynom (list) : list of coefficients (lowest first) 
    """
    class Config(NodeAlias1.Config):
        polynom: List[float] = [0.0,1.0]
        
    
    def fget(self, value):
        if not self.config.polynom:
            return 0.0
        x = self.config.polynom[0]
        for i,c in enumerate(self.config.polynom[1:], start=1):
            x += c*value**i
        return x

PolynomNode = PolynomNode1 



@record_class
class StatisticNode(NodeAlias1):
    class Config(NodeAlias1.Config):
        mean: float = 0.0 # expected mean for Variance and rms computation
        type: str = "Statistic"
        
    @dataclass
    class Stat:
        min  : float = -math.inf
        max  : float =  math.inf
        sum  : float =  math.nan 
        mean : float =  math.nan
        sum2 : float =  math.nan
        rms  : float =  math.nan 
        n    : int = 0
      
    def __init__(self, *args,  **kwargs):                            
        super().__init__(*args, **kwargs)
        self._stat = self.Stat()
        self.reset()
        
    def reset(self):
        s = self._stat
        s.min = -math.inf
        s.max =  math.inf
        s.sum =  math.nan 
        s.mean = math.nan
        s.sum2 = math.nan
        s.rms =  math.nan 
        s.n = 0
        
    def fget(self, value):
        s= self._stat
        if not s.n:
            s.min = value 
            s.max = value 
            s.sum = value
            s.mean = value 
            s.sum2 = (value - self.config.mean)**2
            s.var = s.sum2
            s.rms = value 
            s.n = 1
            
        else:
            s.sum = s.sum+value
            s.sum2 = s.sum2 + (value - self.config.mean)**2
            s.n = s.n+ 1
            s.var = s.sum2/s.n
            s.min = min(value, s.min)
            s.max = max(value, s.max)                         
            s.mean = s.sum/s.n
            s.rms = math.sqrt(s.var) 
            
        return s

class _Stat(NodeAlias1):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
    

@record_class
class SumNode(_Stat):
    class Config(NodeAlias1.Config):        
        type: str = "Sum"
        
    def reset(self):
        self._sum = 0.0
        
    def fget(self, value):
        self._sum += value 
        return self._sum    
        
@record_class
class MeanNode(_Stat):
    class Config(NodeAlias1.Config):        
        type: str = "Mean"
        
    def reset(self):
        self._sum = 0.0
        self._n = 0
    
    def fget(self, value):
        self._sum += value 
        self._n += 1
        return self._sum / self._n

@record_class
class MinNode(_Stat):
    class Config(NodeAlias1.Config):        
        type: str = "Min"
    
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
        
    def reset(self):
        self._min = math.inf
            
    def fget(self, value):
        if value < self._min:            
            self._min = value
        return self._min

@record_class
class MaxNode(_Stat):
    class Config(NodeAlias1.Config):        
        type: str = "Max"
    
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
        
    def reset(self):
        self._max = -math.inf
            
    def fget(self, value):
        if value > self._max:            
            self._max = value
        return self._max



        







        
@record_class
class FormatNode(NodeAlias):
    class Config(NodeAlias.Config):
        type: str = "Format"
        format: str = "{0}"
    
    def fget(self, *values):
        return self.config.format.format(*values)

            
            
            
        
        
