from pydevmgr_core import register, BaseDevice, get_class
import pytest
from pydevmgr_core.base.base import BaseFactory
from systemy import register_factory, get_factory_class

from pydevmgr_core.base.register import record_factory, get_factory
from pydevmgr_core.factories import ObjectFactory
from pydevmgr_core.base.io import load_config, PydevmgrLoader
import yaml


def test_recording_same_class_twice_shoudl_not_raise_error():
    class Dev1(BaseDevice):
        pass

    Dev1 = register("Test2",  Dev1)


def test_record_factory():

    @register
    class Base(BaseDevice):
        ...

    @register_factory('MyFactory', kind="Device")
    class Factory(ObjectFactory):
        ...

    assert get_factory_class( 'MyFactory') == Factory
    
    assert get_factory_class( 'Device/MyFactory') == Factory
    assert get_factory_class( 'MyFactory', kind="Device") == Factory
    
    with pytest.raises(ValueError):
        get_factory_class( 'Node/MyFactory') 

    F = yaml.load("---\n!factory:MyFactory {type: Base, kind: Device}\n", PydevmgrLoader)  
    assert isinstance(F.build() ,  BaseDevice)
    
    F = yaml.load("---\n!factory:Device/MyFactory {type: Base, kind: Device}\n", PydevmgrLoader)  
    assert isinstance(F.build() ,  BaseDevice)



def test_record_factory_with_build():
    
    @register_factory('MyFactory', kind="Device")
    class Factory(BaseFactory):
        def build(self, *args, **kwargs):
            return BaseDevice.Config.parse_obj(self).build(*args, **kwargs)
        
    F = yaml.load("---\n!factory:MyFactory {}\n", PydevmgrLoader)  


    assert isinstance(F.build() ,  BaseDevice)



