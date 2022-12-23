import pytest

from pydevmgr_core import BaseFactory 


def test_update_a_factory():

    class F(BaseFactory, validate_assignment=False):
        a: int = 0
        b: float = 0.0
        def build(self, parent=None, name=None):
            pass

    f = F()

    f.update( a=1, b="1" )
    assert f.b == 1.0
    assert f.__config__.validate_assignment == False

def test_update_factory_with_error():
    class F(BaseFactory, validate_assignment=False):
        a: int = 0
        b: float = 0.0
        def build(self, parent=None, name=None):
            pass

    
    f = F()
    with pytest.raises(ValueError):
        f.update( a="ABC")
    assert f.__config__.validate_assignment == False

