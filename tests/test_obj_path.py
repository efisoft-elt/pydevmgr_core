from pydantic.main import BaseModel
import pytest 
from pydevmgr_core.base.object_path import AttrPath, ObjPath, PathVar, TuplePath 

from pydevmgr_core import BaseManager,  BaseDevice
from systemy import FactoryList, FactoryDict


class Device(BaseDevice, toto=0):
    pass

class M(BaseManager):
        dev_list = FactoryList( [BaseDevice.Config()], BaseDevice.Config)
        dev_dict = FactoryDict( {'d1':Device.Config(toto=1)}, Device.Config)


def test_basic():
    m = M()
    
    assert m.dev_list[0] == ObjPath( "dev_list[0]").resolve(m)
    assert m.connect == ObjPath("connect").resolve(m)
    assert m.dev_dict['d1'] == ObjPath("dev_dict['d1']").resolve(m) 
    assert m.dev_dict['d1'].config.toto ==  ObjPath("dev_dict['d1'].config.toto").resolve(m) 
 

def test_dot_shall_return_parent():
    m = M()
    assert m == ObjPath(".").resolve(m)

def test_hac():
    m = M() 
    with pytest.raises(ValueError):
         ObjPath( 'test()' )

def test_path_var_in_model():
    class A:
        b = 99
    class Data:
        a = A() 

    class M(BaseModel):
        path1: PathVar 
        path2: PathVar 
        path3: PathVar 
        path4: PathVar  
    m = M(path1 = "", path2="a.b", path3="a", path4=("a","b"))
    data = Data()
    assert m.path1.resolve(data) is data 


def test_split_method():
    
    class C:
        x = 9
        l = [1,2]
    class B:
        c = C()
    class A:
        b = B()
    class Root:
        a = A()
    root = Root()

    p = ObjPath("a.b.c")
    assert p.split()[0].resolve(root) is root.a.b
    assert p.split()[1].resolve(root.a.b) is root.a.b.c

    p = TuplePath(("a","b","c"))
    assert p.split()[0].resolve(root) is root.a.b
    assert p.split()[1].resolve(root.a.b) is root.a.b.c
    
    p = AttrPath("a")
    assert p.split()[0].resolve(root) is root
    assert p.split()[1].resolve(root) is root.a

    p = ObjPath("a.b.c.l[0]")
    assert p.split()[0].resolve(root) is root.a.b.c
    assert p.split()[1].resolve(root.a.b.c) == root.a.b.c.l[0]

