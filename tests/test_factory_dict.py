from typing import Dict
from pydevmgr_core import  BaseDevice, BaseNode, KINDS, BaseObject
from systemy import FactoryDict

import pytest

from pydevmgr_core.base.base import ObjectDict 


def test_factory_dict_shall_be_a_auto_member():
    
    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config):
            
            mixed: Dict[str,BaseObject.Config] = {}
    
    
    d = MyDevice()
    assert d.mixed == {}
    

    class Sub(BaseDevice, toto=(int, 0)):
        ...
    
    class MyDevice(BaseDevice):
        class Config:
            mixed: Dict[str, Sub.Config] = {'sub1': Sub.Config() }
    
    d = MyDevice()
    assert d.mixed['sub1'].config.toto == 0

    class Mydevice(BaseDevice):
        mixed = FactoryDict( {'sub1':  Sub.Config() })
    d = MyDevice()
    assert d.mixed['sub1'].config.toto == 0


def test_element_factory_class():

        class MyNode(BaseNode):
            ...

        class Mydevice(BaseDevice):
            class Config(BaseDevice.Config):
                nodes: Dict[str, MyNode.Config] = {}
        
        d = Mydevice(nodes = { 'n1':{}, 'n2':{} } )
        assert isinstance( d.nodes['n1'], MyNode)


def test_factory_dict_can_be_copied():
    class C(BaseDevice.Config):
        toto: int = 0
    f = FactoryDict(  {'d1': C(toto=1), 'd2': C(toto=2)} , C)
    fc = f.copy()
    assert fc['d1'].toto == 1 
    assert fc['d2'].toto == 2 
    fc = f.copy(deep=True)
    assert fc['d1'].toto == 1 
    assert fc['d2'].toto == 2 


