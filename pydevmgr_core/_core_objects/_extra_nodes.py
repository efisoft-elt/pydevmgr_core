from ._core_node import BaseNode, BaseNode
from ._class_recorder import record_class
from typing import Any


class LocalNodeConfig(BaseNode.Config):
    default: Any = None
    type = "Local"

class StaticNodeConfig(BaseNode.Config):    
    type = "Static"
    value: Any
    
@record_class
class StaticNode(BaseNode):
    """ """
    Config = StaticNodeConfig    
    def fget(self):        
        return self.config.value    
    
@record_class
class LocalNode(BaseNode):
    """ A Node getting and setting values inside the localdata dictionary 
    
    The node can only work if its localdata dictionary is an attribute
    """    
    Config = LocalNodeConfig
    def fget(self):
        if self.localdata is None:
            return self.config.default                
        return self.localdata.get(self.key,self.config.default)
        
    def fset(self, value):
        self.localdata[self.key] = value
        
        