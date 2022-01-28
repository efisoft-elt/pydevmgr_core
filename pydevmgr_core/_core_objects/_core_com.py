from pydantic import BaseModel, Extra


class BaseCom: 
    Config = BaseModel
    class Config(BaseModel):
        class Config:
            extra  = Extra.forbid
    
    """ Define a BaseCom object 
    
    The Base does not do anything but is a place holder for what a com object should have
    A Com object can be set into a Device -> Interface -> Node for instance.           
    """ 
    def __init__(self, config=None, **kwargs):
        self._config = self.parse_config(config, **kwargs)
    
    @classmethod
    def parse_config(cls, __config__=None, **kwargs):
        if __config__ is None:
            return cls.Config(**kwargs)
        if isinstance(__config__ , cls.Config):
            return __config__
        if isinstance(__config__, dict):
            return cls.Config( **{**__config__, **kwargs} )
        raise ValueError(f"got an unexpected object for config : {type(__config__)}")
        
    @property
    def config(self):
        return self._config 
    
    def connect(self):
        pass
    
    def disconnect(self):
        pass
    