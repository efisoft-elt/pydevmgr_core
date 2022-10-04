import pytest 
from pydevmgr_core import BaseInterface, BaseNode

class DefaultNode(BaseNode, default=(int, 0), type="Default"):
    def fget(self):
        return self.config.default

def test_interface_node():
    
    class MyInterface(BaseInterface):
        class Config(BaseInterface.Config):
            node1: DefaultNode.Config = DefaultNode.Config( default=1 )            
            node9: DefaultNode.Config = DefaultNode.Config( default=9 )
            
            configured_node  = DefaultNode.Config(default=100)
            configured_node2 = DefaultNode.Config()
            
        not_configured_node = DefaultNode.Config( default=99 )
        
    
        

    i = MyInterface('test')

    assert i.node1.key == 'test.node1'
    assert i.config.node1.default == 1 
    assert i.config.node1 is i.node1.config 
    
    assert i.node1.get() == 1
    assert i.not_configured_node.get() == 99
    assert i.not_configured_node.key == 'test.not_configured_node'
    
    assert i.configured_node.get() == 100
    assert i.configured_node2.get() == 0
    
    assert i.node1 is i.node1


    assert list(sorted( i.children(BaseNode) )) == ['configured_node', 'configured_node2', 'node1', 'node9', 'not_configured_node']

if __name__ == "__main__":
    test_interface_node()   
