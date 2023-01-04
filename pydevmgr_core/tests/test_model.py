import pytest
from build.lib.pydevmgr_core.base.base import BaseData 
from pydevmgr_core import DataLink, BaseManager, BaseDevice, BaseNode, NodeAlias1, NodeVar
from pydevmgr_core.base.base import BaseObject
from pydevmgr_core.base.datamodel import create_data_class
from pydevmgr_core.nodes import Static
from pydantic import BaseModel, Field

from systemy import FactoryList

class Device(BaseDevice):
    class Config(BaseDevice.Config):
        node = Static.Config(value=9.0)


class Device2(BaseDevice):
    class Config(BaseDevice.Config):
        node = Static.Config(value=9.0)
    
    class Data(BaseDevice.Data):
        node: NodeVar[float] = 0.0



class Manager(BaseManager):

    device1 = Device.Config(node={'value':8.0})
    device2 = Device2.Config(node={'value':1.0})

    dev_list = FactoryList( [Device.Config()], Device.Config)

    node = Static.Config(value=99.0)

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

def test_create_model():
    mgr = Manager()
    Data = create_data_class("Data", mgr.find(BaseObject)) 
    data = Data() 
    
    assert data.device1.node is None
    assert data.device2.node == 0.0
    assert data.node is None


    Data = create_data_class("Data", mgr.find(BaseObject), depth=0) 
    data = Data() 
    
    with pytest.raises( AttributeError):
        data.device1
    
    assert data.node is None
