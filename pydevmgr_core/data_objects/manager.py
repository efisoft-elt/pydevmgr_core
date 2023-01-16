from .engine import DataEngine 
from pydevmgr_core.base.manager import BaseManager 
from .node import DataNode 
from .interface import BaseDataInterface 
from .device import BaseDataDevice 

class BaseDataManager(BaseManager):
    class Config(BaseManager.Config, DataEngine.Config):
        pass 
    Engine = DataEngine
    Device = BaseDataDevice 
    Interface = BaseDataInterface
    Node = DataNode
        
    def __init__(self, *args, data=None, **kwargs):
        super().__init__(*args, **kwargs)
        if data is not None:
            self.engine.data = data

