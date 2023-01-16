from .engine import DataEngine 
from pydevmgr_core.base.interface import BaseInterface
from .node import DataNode 
class BaseDataInterface(BaseInterface):
    class Config(BaseInterface.Config, DataEngine.Config):
        pass 
    Engine = DataEngine
    Node = DataNode 


