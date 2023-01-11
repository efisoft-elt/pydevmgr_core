import pytest
from pydevmgr_core import BaseNode, BaseInterface, NodeAlias1, NodeAlias, BaseNodeAlias1
from typing import Any
from pydevmgr_core.base.device import BaseDevice
from pydevmgr_core.base.makers import nodealias_maker
from pydevmgr_core.decorators import nodealias 

from pydevmgr_core.base.manager import BaseManager
from pydevmgr_core.nodes import Static  
from systemy import FactoryList

@pytest.fixture
def MyNode():
    class MyNode(BaseNode, value = (Any, 0.0)):
        def fget(self):
            return self.config.value
        def fset(self, value):
            self.config.value = value
    return MyNode




@pytest.fixture
def node10(MyNode):
    return MyNode(value=10)

@pytest.fixture
def node20(MyNode):
    return MyNode(value=20)

@pytest.fixture
def Scaler():
    class Scaler(NodeAlias1, scale=1.0):
        def fget(self, value):
            return value* self.config.scale
        def fset(self, value):
            yield value/self.config.scale
    return Scaler 


def test_nodealias1_class(node10, Scaler):
    
    scaled = Scaler( node=node10, scale=10.0)
    assert scaled.get() == 100.0
    scaled.set(200)
    assert scaled.get() == 200.0
    assert node10.get() == 20.0

def test_nodealias1_property(MyNode, Scaler):
    class Interface(BaseInterface):
        value = MyNode.Config(value=5.0) 
        scaled =  Scaler.Config( node="value", scale=10.0)

    interface = Interface()
    assert interface.scaled.get() == 50.0

def test_nodealias1_decorator(node10):
    
    @nodealias_maker(node10)
    def offset( value):
        return value+20
    
    assert offset.get() == 30

def test_nodealias1_property_decorator(MyNode):
     class Interface(BaseInterface):
        value1 = MyNode.Config(value=5.0)
        value2 = MyNode.Config(value=4.0)

        @nodealias("value1") 
        def offsetted(self, value):
            return value + 10.0
        
        @nodealias("value1", "value2")
        def squared(self, v1, v2):
            return v1*v2
        
        

     interface = Interface()
     assert interface.offsetted.get() == 15.0  
     assert interface.squared.get() == 4.0*5.0 
     
def test_nodealias_property_decorator(MyNode):
     class Interface(BaseInterface):
        value1 = MyNode.Config(value=5.0)
        value2 = MyNode.Config(value=10.0)
        
        @nodealias("value1", "value2")
        def total(self, value1, value2):
            return value1 + value2 
     
     interface = Interface()
     assert interface.total.get() == 15.0   

def test_embeded_node_alias():

    class Device(BaseDevice, node = Static.Config(value=9)):
        pass

    class Manager(BaseManager):
        dev_list = FactoryList( [Device.Config()], Device.Config)
        node_alias = NodeAlias1.Config(node="dev_list[0].node")


    m = Manager()
    m.node_alias

    assert m.node_alias.get() == m.dev_list[0].node.get()


def test_nodealias_get_set(MyNode):
    bit1 = MyNode(value=False, parser=bool)
    bit2 = MyNode(value=False, parser=bool)
    
    class Num(NodeAlias):
        def fget(self,*bits):
            
            out = 0 
            for bit in bits:
                out = (out << 1) | bit
            return out
        def fset(self, num ):
            out = [bool(num & (1<<i)) for i in range(len(self._nodes))  ]
            return out

    num = Num(nodes=[bit1, bit2])
    assert num.get() == 0
    num.set(1)
    assert bit1.get() is True
    assert bit2.get() is False

    num.set(2)
    assert bit1.get() is False 
    assert bit2.get() is True

    num.set(3)
    assert bit1.get() is True 
    assert bit2.get() is True

def test_bad_number_of_fset_outputs_should_raise_error(node10, node20):
    
    class Dummy(NodeAlias):
        def fget(self, a, b):
            return [a, b]
        def fset(self, l):
            return l
    dummy = Dummy(nodes=[node10, node20])
    assert dummy.get() == [10, 20]
    dummy.set( [100, 200])
    assert dummy.get() == [100, 200]

    with pytest.raises(RuntimeError):
        dummy.set( [10] )
    with pytest.raises(RuntimeError):
        dummy.set( [10, 20, 30] )




            
