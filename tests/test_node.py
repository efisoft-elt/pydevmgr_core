from typing import Type
import pytest

from pydevmgr_core import BaseNode, KINDS
from pydevmgr_core.base.vtype import VType, nodedefault, nodetype

def test_node_ipa():
    node = BaseNode('test') 

    assert node.key == 'test'
    assert node.name == 'test'
    assert node.sid == 0
    assert node.parser is None
    
    assert node.reset() is None

    node.read_collector().add(node)
    node.write_collector().add(node, 0)

    class MyNode(BaseNode):
        _value = 99
        def fget(self):
            return self._value
        def fset(self, new_value):
            self._value = new_value 
         
    mynode = MyNode('test')
    assert mynode.get() == 99
    mynode.set( 10 )
    assert mynode.get() == 10




def test_node_config():

    Config = BaseNode.Config
    
    config = Config() 

    with pytest.raises(ValueError):
        Config(kind="Device")
    
    with pytest.raises(ValueError):
        config.kind = "Device"

    with pytest.raises(ValueError):
        Config( forbiden_extra_value = 8)
    
    
    assert config.get_system_class() is BaseNode

def test_node_type_and_default():

    class N(BaseNode):
        class Config(BaseNode.Config):
            vtype: VType  = int

    assert nodetype(N.Config()) is int
    assert nodedefault(N.Config()) is 0
    
    assert nodetype(N()) is int
    assert nodedefault( N() ) is 0

    assert nodetype(N) is int
    assert nodedefault( N ) is 0


