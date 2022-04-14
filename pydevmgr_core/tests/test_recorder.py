from pydevmgr_core import record_class, BaseDevice, get_class
import pytest 

def test_recording_twice_with_same_type_raise_error():
    @record_class
    class Dev1(BaseDevice, type="Test"):
        pass
    
    assert get_class("Device", "Test") is Dev1

    with pytest.raises(ValueError):
        @record_class
        class Dev2(BaseDevice, type="Test"):
            pass


def test_recording_same_class_twice_shoudl_not_raise_error():
    @record_class
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

