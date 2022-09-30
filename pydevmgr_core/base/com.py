
from dataclasses import dataclass, field


@dataclass
class BaseCom:
    localdata: dict = field(default_factory=dict)
    

    @classmethod
    def new(cls, parent_com, config):
        if parent_com is None:
            return cls()
        return cls(localdata = parent_com.localdata)


