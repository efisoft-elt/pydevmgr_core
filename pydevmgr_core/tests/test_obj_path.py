import pytest 
from pydevmgr_core.base.object_path import ObjPath 

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
 

def test_hac():
    m = M() 
    with pytest.raises(ValueError):
         ObjPath( 'test()' )
