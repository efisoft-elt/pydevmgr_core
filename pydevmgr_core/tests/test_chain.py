import pytest
from pydevmgr_core import BaseManager, BaseDevice, BaseInterface, BaseNode, BaseRpc



class Shared:
    def __init__(self, *args, data=None, **kwargs):
        """ Implement the data argument for all 'My' devices """
        super().__init__( *args, **kwargs)
        self._data = data or {}
    
    @classmethod
    def new_args(cls, parent, name, config) -> dict:
            """ data should be taken from parent """
            args = super().new_args(parent, name, config)
            args["data"] = getattr(parent, "_data", None)
            return args

class MyNode(Shared, BaseNode, data_id=(int, 0)):
    """ A dummy node which takes data from the dictionary from an id """
    def fget(self):
        return self._data[self.config.data_id]
    
    def fset(self, value):
        self._data[self.config.data_id] = value
    

class MyRpc(Shared, BaseRpc, data_id=(int, 0)):  
    """dummy RPC method, its just change a value with data_id """
    def fcall(self, v):
        if not self.config.data_id in self._data:
            return 1
        self._data[self.config.data_id] = v
        return 0 
   
class MyInterface(Shared, BaseInterface):
    class Config(BaseInterface.Config, extra="allow"):
        pass

class MyDevice(Shared, BaseDevice):
    class Config(BaseDevice.Config, extra="allow"):
        pass


@pytest.fixture
def dynamic_motor():
    data = {1:100}
    motor = MyDevice('MOTOR', data=data, STAT=MyInterface.Config( POSITION=MyNode.Config(data_id=1)))
    return motor    


@pytest.fixture
def static_motor():
    data = {1:100}  
    class Stat(MyInterface):
        class Config(MyInterface.Config):
            POSITION : MyNode.Config = MyNode.Config(data_id=1)
            
    class Motor(MyDevice):
        class Config(MyDevice.Config):
            STAT: Stat.Config = Stat.Config()

    motor = Motor("MOTOR", data=data)
    return motor


def test_dynamic_device(dynamic_motor): 
    assert dynamic_motor.STAT.POSITION.get() == 100

def test_static_device(static_motor):
    assert static_motor.STAT.POSITION.get() == 100
    static_motor.STAT.POSITION.set(19.0)
    assert static_motor.STAT.POSITION.get() == 19.0



