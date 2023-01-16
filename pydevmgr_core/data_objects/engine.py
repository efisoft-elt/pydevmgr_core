from pydevmgr_core.base.engine import BaseEngine
from dataclasses import dataclass 
from pydevmgr_core.base.object_path import objpath, PathVar 
from typing import Any, Optional

@dataclass
class DataEngine(BaseEngine):
    data: Optional[Any] = None

    def __post_init__(self):
        if self.data and isinstance(self.data, type):
            self.data = self.data
    
    class Config(BaseEngine.Config):
        data_prefix: Optional[PathVar] = None

    @classmethod
    def new(cls, com, config):
        if isinstance( com, DataEngine):
            data = com.data
        else:
            data = None 
        
        data_prefix = getattr(config, "data_prefix", None)
        if data_prefix:
            data = objpath(config.data_prefix).resolve(data)    
            
        engine = super().new(com, config)
        engine.data = data 
        return engine



@dataclass
class DataNodeEngine(BaseEngine):
    data: Optional[Any] = None
    
    def __post_init__(self):
        if self.data and isinstance(self.data, type):
            self.data = self.data
   
    @classmethod
    def new(cls, com, config):
        if isinstance( com, DataEngine):
            data = com.data
        else:
            data = None 
                
        engine = super().new(com, config)
        engine.data = data 
        return engine

