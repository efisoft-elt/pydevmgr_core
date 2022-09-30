import pytest 
from pydevmgr_core import DataLink, BaseManager, BaseDevice, BaseNode, NodeAlias1, NodeVar
from pydevmgr_core.nodes import Static
from pydantic import BaseModel, Field

from pydevmgr_core.base.factory_list import FactoryList


class Device(BaseDevice):
    class Config(BaseDevice.Config):
        node = Static.Config(value=9.0)
    
class Manager(BaseManager):

    device1 = Device.Config(node={'value':8.0})
    
    dev_list = FactoryList( [Device.Config()], Device.Config)


class Data(BaseModel):
    dev1: NodeVar[float] = Field(0.0, node="device1.node")
    devl0: NodeVar[float] = Field(0.0, node="dev_list[0].node")

    dev1_bis: NodeVar[float] = Field(0.0, node = NodeAlias1.Config(node="device1.node"))
    

def test_node_path():
    
    m = Manager()
    data = Data()
    dl = DataLink( m, data)
    dl.download()
    assert data.dev1 == 8.0
    assert data.devl0 == 9.0 
    data.dev1_bis
    assert data.dev1_bis == data.dev1
 
test_node_path()
