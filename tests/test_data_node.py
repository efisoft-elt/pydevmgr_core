from typing import Optional
from pydevmgr_core import BaseDataDevice, BaseDataInterface, DataNode

    
class Interface(BaseDataInterface):
    val1 = DataNode.Config( data_suffix="val1")
    

class Device(BaseDataDevice):
    i = Interface.Config(data_prefix="i")
    x = DataNode.Config( data_suffix="x")
    ival2 = DataNode.Config( data_suffix="i.val2")

class Data:
    class I:
        val1 = 9
        val2 = 99 
    i = I()
    x: float = 1.0 
    y: float = 0.0 
    
def test_data_value_chain():
    dev = Device()
    data = Data()
    dev.engine.data = data 
    
    assert dev.i.val1.get() == 9 
    dev.i.val1.set(99) 
    assert data.i.val1 == 99
    
    assert dev.x.get() == data.x
    assert dev.ival2.get() == data.i.val2

def test_data_value_dict():
    class I(BaseDataInterface):
        x = DataNode.Config( data_suffix="['x']")
    class Device(BaseDataDevice):
        i = I.Config(data_prefix="['i']")
    
    data = {'i':{'x':6.7}}
    dev = Device(data = data)
    
    assert dev.i.x.get() == 6.7
    assert dev.i.engine.data == data['i']

