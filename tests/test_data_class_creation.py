from typing import Any
from pydantic.fields import Field
from pydantic.main import BaseModel
import pytest
from systemy.system import FactoryList
from pydevmgr_core.base.dataclass import create_data_model
from pydevmgr_core.base.base import BaseObject, find_factories
from pydevmgr_core.base.defaults_var import Defaults
from pydevmgr_core.base.device import BaseDevice
from pydevmgr_core.base.makers import nodealias
from pydevmgr_core.base.manager import BaseManager
from pydevmgr_core.base.model_var import NodeVar
from pydevmgr_core.base.node import BaseNode
from pydevmgr_core.base.node_alias import NodeAlias1
from pydevmgr_core.nodes import Static


class Device(BaseDevice):
    class Config(BaseDevice.Config):
        node: Defaults[Static.Config] = Static.Config(value=9.0, vtype=float)


class Device2(BaseDevice):
    class Config(BaseDevice.Config):
        node = Static.Config(value=9.0, vtype=float)
    
    class Data(BaseDevice.Data):
        node: NodeVar[float] = -9.9


class Manager(BaseManager):

    device1 = Device.Config(node={'value':8.0})
    device2 = Device2.Config(node={'value':1.0})

    dev_list = FactoryList( [Device.Config()], Device.Config)

    node = Static.Config(value=99.0, vtype=None)

class Data(BaseModel):
    dev1: NodeVar[float] = Field(0.0, node="device1.node")
    devl0: NodeVar[float] = Field(0.0, node="dev_list[0].node")

    dev1_bis: NodeVar[float] = Field(0.0, node = NodeAlias1.Config(node="device1.node"))
    

def test_create_model():
    mgr = Manager()
    Data = create_data_model("Data", mgr.find(BaseObject)) 
    data = Data() 
    
    assert data.device1.node == 0.0
    assert data.device2.node == -9.9
    assert data.node is  None


    Data = create_data_model("Data", mgr.find(BaseObject), depth=0) 
    data = Data() 
    
    with pytest.raises( AttributeError):
        data.device1
    
    assert data.node is None


def test_find_classes():
    class Device(BaseDevice):
        n1 = BaseNode.Config()
        n2 = Static.Config()
    result = list(find_factories( Device, BaseNode))

    assert result == [("n1",Device.n1), ("n2",Device.n2)] 
    
    class Device(BaseDevice):
        class Config:
            n1 = BaseNode.Config()
            n2 = Static.Config()

    result = list(find_factories( Device, BaseNode))

    assert result == [("n1",Device.Config().n1), ("n2",Device.Config().n2)]

def test_find_classes_with_nodealias():
    class Device(BaseDevice):
        @nodealias() 
        def n1(self):
            return 1
    result = list(find_factories( Device, BaseNode))
    assert result == [("n1",Device.n1)]

def test_create_data_model_from_class():
    class Device(BaseDevice):
        n1 = BaseNode.Config()
        n2 = Static.Config(vtype=float)
    Data = create_data_model("Data", Device)
    data = Data()
    assert data.n1 is None 
    assert data.n2 == 0.0 


def test_create_data_model_from_factories():
    
    class Device(BaseDevice):
        class Config:
            n1 = BaseNode.Config()
        n2 = Static.Config(vtype=float)
    Data = create_data_model("Data", find_factories(Device, BaseNode))
    data = Data()
    assert data.n1 is None 
    assert data.n2 == 0.0 

def test_create_data_model_with_node_aliases():
    
    class Device(BaseDevice):
        class Config:
            n1 = BaseNode.Config()
        n2 = Static.Config(vtype=float)
        
        @nodealias("n2")
        def isok_annotation(self, n2) -> bool:
            return isinstance(n2, float)
        
        @nodealias("n2", vtype=(bool, True))
        def isok_vtype(self, n2) -> bool:
            return isinstance(n2, float)

    Data = create_data_model("Data", find_factories(Device, BaseNode))
    data = Data()
    assert data.n1 is None 
    assert data.n2 == 0.0 
    assert data.isok_annotation is False 
    assert data.isok_vtype is True 




def test_create_data_model_with_node_model():
    class MyNode(BaseNode):
        class Config:
            min: float = 0.0 
            max: float = 1.0 

    class Device(BaseDevice):
        n1 = MyNode.Config()
        n2 = Static.Config(vtype=float)
    
    class NodeData(BaseModel):
        value: Any = None 
        min: float = -9.99
        max: float = +9.99
    
    Data = create_data_model("Data", Device, NodeModel=NodeData)
    data = Data()
    assert data.n1.value is None 
    assert data.n2.value == 0.0 
    assert data.n1.min == 0.0  
    assert data.n1.max == 1.0 
    
    assert data.n2.min == -9.99
    assert data.n2.max == +9.99 


