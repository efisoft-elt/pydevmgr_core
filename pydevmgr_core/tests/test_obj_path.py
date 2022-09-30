import pytest 
from pydevmgr_core.base.object_path import ObjPath 

from pydevmgr_core import BaseManager, FactoryList, BaseDevice, FactoryDict

class M(BaseManager):
        dev_list = FactoryList( [BaseDevice.Config()], BaseDevice.Config)
        dev_dict = FactoryDict( {'d1':BaseDevice.Config()}, BaseDevice.Config)


def test_basic():
    m = M()
    
    assert m.dev_list[0] == ObjPath( "dev_list[0]").resolve(m)
    assert m.connect == ObjPath("connect").resolve(m)
    assert m.dev_dict['d1'] == ObjPath("dev_dict['d1']").resolve(m) 
    assert m.dev_dict['d1'].config.type ==  ObjPath("dev_dict['d1'].config.type").resolve(m) 
 

def test_hac():
    m = M() 
    with pytest.raises(ValueError):
         ObjPath( 'test()' )
