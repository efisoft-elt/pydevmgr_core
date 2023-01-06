from pydevmgr_core import ParentWeakRef, BaseNode, BaseDevice, BaseInterface, BaseManager
import pytest 

def test_parent_weakref_for_node():
    
    # to test if super new is called 
    class _Node(BaseNode):  
        _test_arg = 0
        @classmethod
        def new(cls, parent, name, config):
            obj = super().new(parent, name, config)
            obj._test_arg = 1
            return obj

    class Node(ParentWeakRef, _Node):
        pass
        

    class Device(BaseDevice):
        node = Node.Config()

    device = Device()
    assert device.node.get_parent() is device
    assert device.node._test_arg == 1 


def test_parent_weakref_for_interface():

    class Interface(ParentWeakRef, BaseInterface):
        pass
    
    class Device(BaseDevice):
        interface = Interface.Config()
    
    device = Device()
    assert device.interface.get_parent() is device

def test_parent_weakref_on_manager():
    class Node(ParentWeakRef, BaseNode):
        pass 

    class Device(ParentWeakRef, BaseDevice):
        node = Node.Config()
        
    class SubManager(ParentWeakRef, BaseManager):
        device = Device.Config()
    
    class Manager(BaseManager):
        mgr = SubManager.Config()

    mgr = Manager()
    assert mgr.mgr.get_parent() == mgr 
    assert mgr.mgr.device.get_parent() == mgr.mgr 
    assert mgr.mgr.device.node.get_parent() == mgr.mgr.device



        
    
