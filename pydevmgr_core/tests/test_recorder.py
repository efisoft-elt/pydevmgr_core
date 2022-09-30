from pydevmgr_core import record_class, BaseDevice, get_class
import pytest
from pydevmgr_core.base.base import BaseFactory

from pydevmgr_core.base.class_recorder import record_factory, get_factory
from pydevmgr_core.base.factory_object import ObjectFactory
from pydevmgr_core.base.io import load_config, PydevmgrLoader
import yaml

def test_recording_twice_with_same_type_raise_error():
    @record_class
    class Dev1(BaseDevice, type="TestR1"):
        pass
    
    assert get_class("Device", "TestR1") is Dev1

    with pytest.raises(ValueError):
        @record_class
        class Dev2(BaseDevice, type="TestR1"):
            pass


def test_recording_same_class_twice_shoudl_not_raise_error():
    class Dev1(BaseDevice, type="Test2"):
        pass

    Dev1 = record_class(Dev1)

def test_recording_overwrite_should_not_raise():
    @record_class
    class Dev1(BaseDevice, type="Test3"):
        pass
    
    assert get_class("Device", "Test3") is Dev1

    @record_class(overwrite=True)
    class Dev2(BaseDevice, type="Test3"):
        pass



def test_record_factory():
    
    @record_factory('MyFactory', kind="Device")
    class Factory(ObjectFactory):
        ...

    assert get_factory( 'MyFactory') == Factory
    
    assert get_factory( 'Device:MyFactory') == Factory
    assert get_factory( 'Device', 'MyFactory') == Factory
    
    with pytest.raises(ValueError):
        get_factory( 'Node:MyFactory') 

    F = yaml.load("---\n!F:MyFactory {type: Base, kind: Device}\n", PydevmgrLoader)  
    assert isinstance(F.build() ,  BaseDevice)
    
    F = yaml.load("---\n!F:Device:MyFactory {type: Base, kind: Device}\n", PydevmgrLoader)  
    assert isinstance(F.build() ,  BaseDevice)



def test_record_factory_with_build():
    
    @record_factory('MyFactory', kind="Device")
    class Factory(BaseFactory):
        def build(self, *args, **kwargs):
            return BaseDevice.Config.parse_obj(self).build(*args, **kwargs)
        
    F = yaml.load("---\n!F:MyFactory {}\n", PydevmgrLoader)  


    assert isinstance(F.build() ,  BaseDevice)



