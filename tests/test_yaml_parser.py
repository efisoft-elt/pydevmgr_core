import pytest
from pydevmgr_core.base.io import PydevmgrLoader, find_config
from pydevmgr_core import ObjectFactory, BaseNode,  BaseDevice, BaseManager, BaseInterface
from pydevmgr_core.nodes import Static
import yaml 
from systemy import FactoryDict, register_factory




@register_factory("Node/Test")
class Node(BaseNode):
    class Config:
        value = 9.0
    def fget(self):
        return self.value 
    
    def fset(self, value):
        self.config.value = value 

@register_factory("Device/Test")
class Motor(BaseDevice, 
            prefix = "default",
            x=9.99  
    ):
    pass


@register_factory("Interface/Test")
class Interface(BaseInterface):
    class Config(BaseInterface.Config, extra="allow"):
        n: Static.Config = Static.Config(value=0.0)
        


@register_factory("Manager/Test")
class Manager(BaseManager):
    class Config(BaseManager.Config):

        interface3: Interface.Config = Interface.Config()
        class Config:
            extra = "allow"




# text1 = """--- 
# motor1: !include:tins/motor1.yml(motor1)
#     prefix: "TOTO"
# """

text2 = """---
x: !math 3*4
"""


text3 = """---
motor: !factory:Device/Test
    prefix: "MAIN.M1"
"""

text4 = """---
motor: !factory:Device/Test
    prefix: "MAIN.M1"
"""

text5 = """---
motor: !factory:Device/Test
    prefix: "MAIN.M1"
"""

text6 = """---
motor: !factory:Device/Test
    prefix: "MAIN.M1"
    unknown_field: 10 
"""






# def test_load_include_file():

#     try: # do not execute this test if file cannot be found 
#         find_config('tins/motor1.yml')
#     except Exception:
#         return 
#     d = yaml.load( text1, PydevmgrLoader)
#     assert d['motor1']['prefix'] == "TOTO"
#     assert d['motor1']['type'] == "Motor"


def test_math():
    d = yaml.load( text2, PydevmgrLoader)
    assert d['x'] == 12

def test_factory():
    d = yaml.load( text3, PydevmgrLoader)
    motor = d['motor'].build(None)
    assert motor.config.prefix == "MAIN.M1"

def test_device_factory():
    d = yaml.load( text4, PydevmgrLoader)
    motor = d['motor'].build(None)
    assert motor.config.prefix == "MAIN.M1"

def test_device_factory_in_tag():
    d = yaml.load( text5, PydevmgrLoader)
    motor = d['motor'].build(None)
    assert motor.config.x == 9.99
    assert motor.config.prefix == "MAIN.M1"

def test_extra_config_value_must_be_catched_at_init():
    with pytest.raises(ValueError):
        d = yaml.load( text6, PydevmgrLoader)
