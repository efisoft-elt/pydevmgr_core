from dataclasses import dataclass, field

from pydantic.main import BaseModel

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

if __name__ == "__main__":
    BaseEngine()
