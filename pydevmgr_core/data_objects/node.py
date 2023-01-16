from .engine import  DataNodeEngine
from pydevmgr_core.base.register import register 
from pydevmgr_core.base.node import BaseNode 
from pydevmgr_core.base.object_path import PathVar
from typing import Any, Optional

class __Undefined__:
    pass 

@register
class DataNode(BaseNode):
    """ node is getting/setting from the data structure found inside the engine 
    The targeted node is resolved from the data_suffix attribute 
    """
    Engine = DataNodeEngine 
    
    class Config:
        data_suffix: PathVar 
        default: Any = __Undefined__ 
    
    def fget(self):
        try:
            value = self.data_suffix.resolve(self.engine.data)
        except AttributeError as e:
            if self.default is __Undefined__:
                raise e
            else:
                value = self.default 
        return value
    
    def fset(self, value):
        self.data_suffix.set_value( self.engine.data, value)
         


