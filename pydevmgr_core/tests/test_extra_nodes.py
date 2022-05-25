from pydevmgr_core import  BaseNode
from pydevmgr_core.nodes import AllTrue, AnyTrue, AnyFalse, AllFalse

from pydevmgr_core import nodes
import time 
import pytest 
from typing import Any 

# testing only latest (v0.5) alias nodes 

@pytest.fixture
def MyNode():
    class MyNode(BaseNode, value = (Any, 0.0)):
        def fget(self):
            return self.config.value
        def fset(self, value):
            self.config.value = value
    return MyNode

@pytest.fixture
def node_true(MyNode):
    return MyNode(value=True, parser=bool)

@pytest.fixture
def node_false(MyNode):
    return MyNode(value=False, parser=bool)

def test_bit_node(MyNode):
    b0 =  MyNode(value=True)
    b1 =  MyNode(value=False)
    b2 =  MyNode(value=True)

    b = nodes.Bits( nodes=[b0,b1,b2])
    assert b.get() == 5
    b.set(3)
    assert b0.get() is True
    assert b1.get() is True 
    assert b2.get() is False
    assert b.get() == 3
    b.set(1)
    assert b0.get() is True
    assert b1.get() is False 
    assert b2.get() is False
    assert b.get()==1
    b.set(2)
    assert b0.get() is False
    assert b1.get() is True 
    assert b2.get() is False
    assert b.get() == 2


def text_max_of(MyNode):
    max = nodes.MaxOf( nodes = [MyNode(value=v) for v in [2,10,3] ])
    assert max.get() == 10

def text_min_of(MyNode):
    min = nodes.MinOf( nodes = [MyNode(value=v) for v in [2,10,3] ])
    assert min.get() == 2

def test_mean_of(MyNode):
    mean = nodes.MeanOf( nodes = [MyNode(value=v) for v in [2,4,6] ])
    assert mean.get() == 4.0


def test_all_true(MyNode):

    assert AllTrue( nodes=[ MyNode(value=True),  MyNode(value=True) ]).get()
    assert not AllTrue( nodes=[ MyNode(value=False),  MyNode(value=True) ]).get() 

def test_any_true(MyNode):
    assert AnyTrue( nodes=[ MyNode(value=True),  MyNode(value=True) ]).get()
    assert AnyTrue( nodes=[ MyNode(value=False),  MyNode(value=True) ]).get()
    assert not AnyTrue( nodes=[ MyNode(value=False),  MyNode(value=False) ]).get()

def test_any_false(MyNode):
    assert not AnyFalse( nodes=[ MyNode(value=True),  MyNode(value=True) ]).get()
    assert AnyFalse( nodes=[ MyNode(value=False),  MyNode(value=True) ]).get()
    assert AnyFalse( nodes=[ MyNode(value=False),  MyNode(value=False) ]).get()

def test_all_false(MyNode):
    assert not AllFalse( nodes=[ MyNode(value=True),  MyNode(value=True) ]).get()
    assert not AllFalse( nodes=[ MyNode(value=False),  MyNode(value=True) ]).get()
    assert AllFalse( nodes=[ MyNode(value=False),  MyNode(value=False) ]).get()


def test_sum():
    s = nodes.Sum( node=nodes.Counter())
    assert s.get() == 1.0
    assert s.get() == 3.0
    assert s.get() == 6.0
    s.reset() 
    assert s.get() == 4.0

def test_mean():
    m = nodes.Mean( node=nodes.Counter())
    assert m.get() == 1.0
    assert m.get() == 1.5
    assert m.get() == 2.0 
    m.reset()
    assert m.get() == 4.0

def test_min():
    v = nodes.Value(value=2.0)
    m  = nodes.Min( node=v)
    assert  m.get()==2.0
    v.set(10.0) 
    assert m.get() == 2.0
    v.set(1.0)
    assert m.get() == 1.0


def test_max():
    v = nodes.Value(value=2.0)
    m  = nodes.Max( node=v)
    assert  m.get()==2.0
    v.set(10.0) 
    assert m.get() == 10.0
    v.set(1.0)
    assert m.get() == 10.0

def test_format():

    f = nodes.Format( nodes=[nodes.Value(value=4.56), nodes.Value(value="meter")], format="{0:.1f} {1}" )
    assert f.get() == "4.6 meter"


def test_elapsed_time():
    t = nodes.ElapsedTime()
    t.get()
    time.sleep(1.0)
    assert t.get()>1.0 
