import pytest 
from pydevmgr_core.base.node_alias import _guess_number_of_nodes
from pydevmgr_core import NodeAlias 

def test_simple_func():
    
    class A:
        def fget(self, value1):
            pass
    assert _guess_number_of_nodes(A) == 1

    class A:
        def fget(self, value1, value2):
            pass
    assert _guess_number_of_nodes(A) == 2
    

    class A:
        def fget(self):
            pass
    assert _guess_number_of_nodes(A) == 0

def test_static_method():
    class A:
        @staticmethod
        def fget(value1):
            pass
    assert _guess_number_of_nodes(A) == 1

def test_class_method():
    class A:
        @classmethod
        def fget(cls, value1):
            pass
    assert _guess_number_of_nodes(A) == 1

def test_undefined_number_of_args():
    class A:
        def fget(self, *args):
            pass
    assert _guess_number_of_nodes(A) is None
    
    class A:
        def fget(self, *args, **kwargs):
            pass
    assert _guess_number_of_nodes(A) is None

def test_with_kwargs():
    
    class A:
        def fget(self, **kwargs):
            pass
    assert _guess_number_of_nodes(A) == 0
   
    
    class A:
        def fget(self, value1=None, value2=None):
            pass
    assert _guess_number_of_nodes(A) == 2

    class A:
        def fget(self, value1=None, *, value2=None):
            pass
    assert _guess_number_of_nodes(A) == 1




def test_on_node():
    
    class N(NodeAlias):
        def fget(self, a,b,c):
            pass
    assert N._n_nodes_required == 3
    
    
    class N2(NodeAlias):
        @staticmethod
        def fget( a,b,c):
            pass
    assert N2._n_nodes_required == 3
    
    
    
    class N3(N):
        def fget(self, a,b):
            pass

    assert N3._n_nodes_required == 2
    
    class N4(N3):
        def fget(self, a, *, k1=0):
            pass
    assert N4._n_nodes_required == 1
    
    with pytest.raises(ValueError):
        N( nodes=[])
