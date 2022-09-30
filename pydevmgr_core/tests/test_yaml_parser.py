import pytest
from pydevmgr_core.base.factory_dict import FactoryDict 
from pydevmgr_core.base.io import PydevmgrLoader, find_config
from pydevmgr_core import ObjectFactory, BaseNode, record_class, BaseDevice, BaseManager, BaseInterface
from pydevmgr_core.nodes import Static
import yaml 




@record_class(overwrite=True)
class Node(BaseNode):
    class Config:
        type = 'Test' 
        value = 9.0
    def fget(self):
        return self.value 
    
    def fset(self, value):
        self.config.value = value 

@record_class(overwrite=True)
class Motor(BaseDevice, 
            prefix = "default",
            x=9.99,  
            type="Test"
    ):
    pass


    
@record_class(overwrite=True)
class Interface(BaseInterface):
    class Config(BaseInterface.Config, extra="allow"):
        type = "Test"
        n: Static.Config = Static.Config(value=0.0)
        


@record_class(overwrite=True, yaml_tag="!MyManager")
class Manager(BaseManager):
    class Config(BaseManager.Config):
        type = "Test"

        interface3: Interface.Config = Interface.Config()
        class Config:
            extra = "allow"




text1 = """--- 
motor1: !include:tins/motor1.yml(motor1)
    prefix: "TOTO"
"""

text2 = """---
x: !math 3*4
"""


text3 = """---
motor: !F:
    type: Test
    kind: Device
    prefix: "MAIN.M1"
"""

text4 = """---
motor: !F:Device
    type: Test
    prefix: "MAIN.M1"
"""

text5 = """---
motor: !F:Device:Test
    prefix: "MAIN.M1"
"""

text6 = """---
motor: !F:Device:Test
    prefix: "MAIN.M1"
    unknown_field: 10 
"""




text7 = """---
!F:Manager:Test
    motor: !F:Device:Test
        prefix: MAIN.M1
    interface: !F:Interface:Test {}
    interface2: !F:Interface:Test
        n: 
            value: 9.0
        n2: !F:Node:Test
            value: 100
    interface3: 
        n: 
            value: -99.99
    
"""

text8 = """---
!MyManager
    motors: !FactoryDict:Device:Test {
        m1: {},
        m2: {prefix: 'MAIN.M2'}
        }
"""

text9 = """---
!F:Manager:Test
    motors: !FactoryList:Device:Test [
        {},
        {prefix: 'MAIN.M2'}
    ]
"""

text10 = """---
!F:Manager:Test
    motors: !FactoryList:Device
         - {type: Test}
         - !F:Device:Test {prefix: 'MAIN.M2'}
    
"""

text11 = """---
!F:Manager:Test
    motors: !FactoryDict:Device {
        m1: {type: Test},
        m2: !F:Device:Test {type: Test, prefix: 'MAIN.M2'}, 
        m3: {type: Test, prefix: MAIN.M3}
        }
"""


def test_load_include_file():

    try: # do not execute this test if file cannot be found 
        find_config('tins/motor1.yml')
    except Exception:
        return 
    d = yaml.load( text1, PydevmgrLoader)
    assert d['motor1']['prefix'] == "TOTO"
    assert d['motor1']['type'] == "Motor"


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
    

def test_manager_parsing():
    mf = yaml.load( text7, PydevmgrLoader)
    m = mf.build()
    assert m.motor.config.prefix == "MAIN.M1"
    assert m.config.motor.prefix == "MAIN.M1"
    # assert m.interface.n.get() == 0.0
    # assert m.interface2.n.get() == 9.0
    assert m.interface2.n2.get() == 100.0
    assert m.interface3.n.get() == -99.99

    m.interface2.n2.set( 200) 

    assert m.interface2.n2.get() == 200.0
# test_manager_parsing()


def test_factory_dict_parsing():
    mf = yaml.load( text8, PydevmgrLoader)
    m = mf.build()
    assert m.motors['m1'].config.prefix == "default"
    assert m.motors['m2'].config.prefix == "MAIN.M2"



def test_factory_list_parsing():
    mf = yaml.load( text9, PydevmgrLoader)
    m = mf.build()
    assert m.motors[0].config.prefix == "default"
    assert m.motors[1].config.prefix == "MAIN.M2"

 
def test_factory_list_parsing_with_default_factory():
    mf = yaml.load( text10, PydevmgrLoader)
    m = mf.build()
    assert m.motors[0].config.prefix == "default"
    assert m.motors[1].config.prefix == "MAIN.M2"

def test_factory_dict_parsing_with_defula_factory():
    mf = yaml.load( text11, PydevmgrLoader)
    m = mf.build()
    assert m.motors['m1'].config.prefix == "default"
    assert m.motors['m2'].config.prefix == "MAIN.M2"
    assert m.motors['m3'].config.prefix == "MAIN.M3"

# test_factory_dict_parsing_with_defula_factory()


test_manager_parsing()
# import yaml

# def _cons(loader, flag, node):
#     print(node)
#     d = {}
#     for i,e in enumerate(node.value):
#         print('-', i, e)
#         k, v = e 
#         v = loader.construct_mapping( v)
#         d[k.value] = v
#     return FactoryDict(d, Motor.Config)
# yaml.add_multi_constructor( "!Toto", _cons, PydevmgrLoader)


# print( yaml.load( text9, PydevmgrLoader))
