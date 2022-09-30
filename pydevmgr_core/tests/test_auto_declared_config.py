from pydevmgr_core import BaseDevice, BaseNode 
from pydevmgr_core import nodes



class Device(BaseDevice):
    class Config:
        address: str = ""
        node = nodes.Static.Config(value=9)

class SubDevice(Device):
    pass



def test_auot_config():

    d = Device(address=999)
    assert d.config.address == "999"
    assert d.node.get() == 9
    
    d2 = SubDevice()
    assert d2.node.get() == 9

