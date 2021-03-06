from pydevmgr_core import BaseDevice, BaseNode, BaseManager
import pytest 


class MyNode(BaseNode):
    def __init__(self, *args, data=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data         
    
    @classmethod
    def new_args(cls, parent, name, config):
        d = super().new_args(parent, name, config)
        d['data'] = parent.data
        return d 

    def fget(self):
        return self.data[0][self]
    def fset( self, value):
        self.data[0][self] = value
        
class MyDevice(BaseDevice):
    n = MyNode.prop()
    data = []
    def connect(self):
        self.data = [{}]
    def disconnect(self):
        self.data = []



def test_with_statment_should_connect():
    with MyDevice() as d:
        d.n.set(10)
        assert d.n.get() == 10
        
def test_after_with_should_be_disconnected():
    d = MyDevice()
    with d:
        pass
    assert d.data == []
    
def test_with_manager():
    class Manager(BaseManager):
        d = MyDevice.prop()

    with Manager() as m: 
        m.d.n.set(10)
        assert m.d.n.get() == 10

def test_error_inside_with_should_be_raised():
    with pytest.raises(AttributeError): 
        with MyDevice() as d:
            d.not_a_node
    assert d.data == []
         



