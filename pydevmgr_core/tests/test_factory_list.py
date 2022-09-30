import pytest 
from pydevmgr_core import FactoryList, BaseDevice, BaseNode, KINDS

def test_factory_list_are_auto_members():

    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config):
            
            mixed: FactoryList = FactoryList()
    
    d = MyDevice()
    assert d.mixed == []
    assert d.mixed is d.mixed
    
    d = MyDevice( mixed = [BaseDevice.Config(), BaseNode.Config()] )
    assert d.mixed[0].config.kind == KINDS.DEVICE
    assert d.mixed[1].config.kind == KINDS.NODE

def test_factory_list_with_factory_class():

    class MySubDevice(BaseDevice):
        class Config(BaseDevice.Config):
            new_value = 0.0

    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config):
            sub_devices: FactoryList[MySubDevice.Config] = FactoryList()
             

    c =  MyDevice.Config( sub_devices= [{}, {'new_value':9.9}]  ) #
    d = MyDevice(config=c) 
    # print( 'AAA', MyDevice.Config(sub_devices=[{}]).sub_devices)

    assert d.sub_devices[0].config.new_value == 0.0

    assert d.sub_devices[1].config.new_value == 9.9


def test_factory_list_member_are_findable():

    class MySubDevice(BaseDevice):
        class Config(BaseDevice.Config):
            type = "SubDevice"
            new_value = 0.0

    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config):
            type = "MyDevice"
            sub_devices: FactoryList[MySubDevice.Config] = FactoryList()
             
    c =  MyDevice.Config( sub_devices= [{}, {'new_value':9.9}]  ) #
    d = MyDevice(config=c) 
   

    
    assert len(list(d.find( MySubDevice, -1))) == 2
     
    list(d.find( MySubDevice, -1))[0] == d.sub_devices[0]


def test_factory_list_can_be_copied():
    class C(BaseDevice.Config):
        toto: int = 0
    f = FactoryList(  [{'toto':1}, {'toto':2}] , C)
    fc = f.copy()
    assert fc[0].toto == 1 
    assert fc[1].toto == 2 
    assert fc.Factory == C
    fc = f.copy(deep=True)
    assert fc[0].toto == 1 
    assert fc[1].toto == 2 
    assert fc.Factory == C  


