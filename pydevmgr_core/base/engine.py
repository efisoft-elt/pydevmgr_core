from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic.main import BaseModel

from pydevmgr_core.base.object_path import objpath, PathVar 

@dataclass
class BaseEngine:
    localdata: dict = field(default_factory=dict)
    
    class Config(BaseModel):
        pass
    
    @classmethod
    def new(cls, com, config):
        if com is None:
            return cls()
        return cls(localdata = com.localdata)

@dataclass
class BaseEngineWithData(BaseEngine):
    data: Optional[Any] = None

    def __post_init__(self):
        if self.data and isinstance(self.data, type):
            self.data = self.data
    
    class Config(BaseEngine.Config):
        data_prefix: Optional[str] = None

    @classmethod
    def new(cls, com, config):
                
        if isinstance( com, BaseEngineWithData):
            data = com.data
        else:
            data = None 
        
        data_prefix = getattr(config, "data_prefix", None)
        if data_prefix:
            data = objpath(config.data_prefix).resolve(data)    
            
        engine = super().new(com, config)
        engine.data = data 
        return engine
        


if __name__ == "__main__":
    BaseEngine()
