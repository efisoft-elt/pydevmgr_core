""" some nodes that required numpy to be executed if numpy is not installed theses nodes will not be loaded """

from ._core_objects import  BaseNode, NodeAlias, NodeAlias1, record_class
from collections import deque
from typing import Optional, List, Tuple
import numpy as np
from enum import Enum 

__all__ = [
"NoiseNode",
"NoiseAdderNode",
"HistogramNode",
"MeanFilterNode", 
"MaxFilterNode", 
"MinFilterNode", 
"VarianceFilterNode", 
"RmsFilterNode", 
"MedianFilterNode", 
"PickToValleyFilterNode"
]

def random(mean, scale, size):
    return np.random.random(size)*scale+mean


class RANDOM_FUNC(Enum):
    RANDOM = "random"
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
RANDOM_FUNC.RANDOM.func = random
RANDOM_FUNC.NORMAL.func = np.random.normal
RANDOM_FUNC.LOGNORMAL.func = np.random.lognormal

@record_class
class NoiseNode(BaseNode):
    class Config(BaseNode.Config):
        type: str = "Noise"
        mean: float = 0.0 # Mean ("centre") of the distribution
        scale: float = 1.0 # Standard deviation (spread or "width") of the distribution
        size: Optional[List[int]] = None
        distribution: RANDOM_FUNC = RANDOM_FUNC.NORMAL
    
    def fget(self):
        c = self.config
        return RANDOM_FUNC(c.distribution).func(c.mean, c.scale, c.size)
        
@record_class
class NoiseAdderNode(NodeAlias1):
    class Config(NodeAlias1.Config):
        type: str = "NoiseAdder"
        scale: float = 1.0 # Standard deviation (spread or "width") of the distribution
        distribution: RANDOM_FUNC = RANDOM_FUNC.NORMAL
    
    def fget(self, value):
        c = self.config
        return RANDOM_FUNC(c.distribution).func(value, c.scale)
        
@record_class
class HistogramNode(NodeAlias1):
    class Config(NodeAlias1.Config):
        type: str = "Histogram"
        bins: Tuple[float,float,int] = (-100,100,100)        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
    def reset(self):
        min,max,n = self.config.bins
        self._bins = np.linspace(min,max,n)
        self._hist = [0]*(len(self._bins)-1)
        
    def fget(self, value):
        min,max,_ = self.config.bins
        if value<min or value>max:
            return self._hist
        i = np.digitize(value, self._bins)    
        self._hist[i-1] += 1
        return self._hist
            

class _Filter(NodeAlias1):
    class Config(NodeAlias1.Config):
        nval : int = 10
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = deque([], self.config.nval)
    
    def fget(self, value):
        self._data.append(value)
        return self._func(self._data)

@record_class
class MeanFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "MeanFilter"    
    _func = staticmethod(np.mean)    

@record_class
class MaxFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "MaxFilter"    
    _func = staticmethod(np.max)  
      
@record_class
class MinFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "MinFilter"    
    _func = staticmethod(np.min)

@record_class
class VarianceFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "VarianceFilter"
    @staticmethod
    def _func(data):
        data = np.asarray(data)
        m = np.mean(data)
        return (data-m)**2/len(data)

@record_class
class RmsFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "RmsFilter"
    @staticmethod
    def _func(data):
        data = np.asarray(data)
        m = np.mean(data)
        return np.sqrt(  (data-m)**2/len(data) )         

@record_class
class MedianFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "MedianFilter"    
    _func = staticmethod(np.median)

@record_class
class PickToValleyFilterNode(_Filter):
    class Config(_Filter.Config):
        type = "PickToValleyFilter"
    @staticmethod
    def _func(data):
        return  np.max(data)-np.min(data)  
   
        
