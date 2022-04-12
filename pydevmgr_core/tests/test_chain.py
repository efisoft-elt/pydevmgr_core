import pytest
from pydevmgr_core import BaseManager, BaseDevice, BaseInterface, BaseNode, BaseRpc



class Shared:
    def __init__(self, *args, data=None, **kwargs):
        super().__init__( *args, **kwargs)
        self._data = data or {}
    
    @classmethod
    def new_args(cls, parent, config) -> dict:
            args = super().new_args(parent, config)
            args["data"] = getattr(parent, "_data", None)
            return args

class MyNode(Shared, BaseNode):
    def fget(self):
        return self._data[self.key]
    
    def fset(self, value):
        self._data[self.key] = value
    

class MyRpc(Shared, BaseRpc):  
    def fcall(self, v):
        self._data[self.key] = v
   
class MyInterface(Shared, BaseInterface):
    class Config(BaseInterface.Config, extra="allow"):
        pass

class MyDevice(Shared, BaseDevice):
    class Config(BaseDevice.Config, extra="allow"):
        pass
    
data = {"MOTOR.STAT.POSITION": 9.0}

def test_dynamic_device():
    motor = MyDevice('MOTOR', data=data, STAT=MyInterface.Config( POSITION=MyNode.Config()))
    assert motor.STAT.POSITION.get() == 9.0

def test_static_device():
    
    class Stat(MyInterface):
        class Config(MyInterface.Config):
            POSITION : MyNode.Config = MyNode.Config()
            
    class Motor(MyDevice):
        class Config(MyDevice.Config):
            STAT: Stat.Config = Stat.Config()

    motor = Motor("MOTOR", data=data)
    assert motor.STAT.POSITION.get() == 9.0
    motor.STAT.POSITION.set(19.0)
    assert motor.STAT.POSITION.get() == 19.0



