from dataclasses import dataclass

from pydantic.main import BaseModel
from pydevmgr_core import BaseDevice, DataLink, NodeVar, StaticVar
from pydevmgr_core.nodes import Value 


class SubDevice(BaseDevice):
    a = Value.Config(value="a")
    b = Value.Config(value="b")

class Device(BaseDevice):

    v1 = Value.Config(value=1)
    v2 = Value.Config(value=2)
    
    sub = SubDevice.Config()




def test_simple_class():
    class Data:
        v1: NodeVar[float] = 0.0
        v2: NodeVar[float] = 0.0
        
        some_param = None
        class Sub:
            a: NodeVar[str] = ""
            b: NodeVar[str] = ""
        sub = Sub()

    dev = Device()
    data = Data()
    dl = DataLink( dev, data) 
    dl.download()
    
    assert data.v1 == dev.v1.get()
    assert data.sub.a == dev.sub.a.get()



def test_with_data_class():
    @dataclass
    class Data:
        v1: NodeVar[float] = 0.0
        v2: NodeVar[float] = 0.0
        key: StaticVar[str] = "" 
        some_param = None
        class Sub:
            a: NodeVar[str] = ""
            b: NodeVar[str] = ""
        sub = Sub()

    dev = Device("mydevice")
    data = Data()
    dl = DataLink( dev, data) 
    dl.download()
    
    assert data.v1 == dev.v1.get()
    assert data.sub.a == dev.sub.a.get()
    assert data.key == dev.key 

def test_node_data():
    class Data:
        value = 0.0
        key: StaticVar  = ""

    v = Value('v', value=10)
    data = Data() 

    dl = DataLink( v,data)
    dl.download()
    
    assert data.value == v.get()
    assert data.key == v.key 
