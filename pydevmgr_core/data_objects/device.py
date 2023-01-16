from .engine import DataEngine 
from pydevmgr_core.base.device import BaseDevice 
from .node import DataNode 
from .interface import BaseDataInterface 
class BaseDataDevice(BaseDevice):
    class Config(BaseDevice.Config, DataEngine.Config):
        pass 
    Engine = DataEngine
    Interface = BaseDataInterface
    Node = DataNode

    def __init__(self, *args, data=None, **kwargs):
        super().__init__(*args, **kwargs)
        if data is not None:
            self.engine.data = data

