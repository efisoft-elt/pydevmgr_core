from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic.main import BaseModel


@dataclass
class BaseEngine:
    localnode_values: dict = field(default_factory=dict)
    
    class Config(BaseModel):
        pass
    
    @classmethod
    def new(cls, com, config: Config):
        if com is None:
            return cls()
        return cls(localnode_values = com.localnode_values)

        
@dataclass
class BaseNodeEngine:
    localnode_values: dict = field(default_factory=dict)
    class Config(BaseModel):
        pass
    
    @classmethod
    def new(cls, com, config: Config):
        if com is None:
            return cls()
        return cls(localnode_values = com.localnode_values)


if __name__ == "__main__":
    BaseEngine()
