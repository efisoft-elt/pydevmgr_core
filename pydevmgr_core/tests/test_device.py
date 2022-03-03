from pydevmgr_core import BaseDevice, StaticNode, BaseInterface, to_nodealias_class, to_rpc_class
from pydevmgr_core import NodeAlias, NodeAlias1, record_class, get_class, BaseRpc, FormulaNode

import yaml


@record_class
class Ctrl(BaseInterface):
    class Config(BaseInterface.Config):
        type  = "Control"
        description = "This is something"
    go = StaticNode.prop('go', value=True)


@record_class(overwrite=True)
class Printer(BaseRpc):
    class Config(BaseRpc.Config):
        type  = "Printer"
    def fcall(self, *args):
        print(self.key, 'called with args', args)

@record_class(overwrite=True)
@to_rpc_class
def Printer2(key, *args):
    print(key, 'called with args', args)


@record_class(overwrite=True)
class Scaler(NodeAlias1):
    class Config(NodeAlias1.Config):
        scale: float  = 100.0
        type: str =  "Scaler"
        dummy: int = 1
        
    def fget(self, value):
        return self.config.scale*value

@record_class(overwrite=True)
@to_nodealias_class
def Scaler2(value, scale:float = 100.0, dummy: int = 2):
    return value * scale
        
@record_class(overwrite=True)            
class MyDevice(BaseDevice):
    class Config(BaseDevice.Config):
        type: str = "MyDevice"    
    
    purestatic    = StaticNode.prop(value=9) # try without a name 
    changedstatic = StaticNode.prop('chs', value=9) # with a name 
    @NodeAlias1.prop('plus', 'purestatic')
    def plus(self, ps):
        return ps+10
    
    hundred = Scaler.prop('hundred', 'purestatic')
    fifty = get_class("Node", "Scaler2").prop('fifty', 'purestatic', scale=80, dummy=2)
    
    cfg = BaseInterface.prop('cfg', node_map={'alpha':{'type':'Static', "value":9}})
    ctrl = Ctrl.prop('ctrl')
    
    
cfg_txt = """---
node_map:
    temperature_volt: 
       kind: Node
       type: Static
       value: 1.0
    temperature:
       type: Formula
       formula: 24.0 * t - 2.0
       nodes: ['temperature_volt']
       varnames: [t]
    humidity: 
       kind: Node
       type: Static
       value: 54.0
    chs:
       kind: Node
       type: Static
       value: 19
    hundred:
        type: Scaler
    fifty:
        type: Scaler2
        scale: 50
    fifty2:
        type: Scaler
        scale: 50
        node: temperature
       
rpc_map:
    echo:
        type: Printer    
    echo2:
        type: Printer2    
interface_map:
    stat:
        kind: Interface
        node_map:
            status:
                kind: Node
                type: Static
                value: 10
    ctrl2:
        type: Control
        description: This is something else    
"""

def test_main():  
    config = MyDevice.Config.parse_obj(yaml.load(cfg_txt, yaml.CLoader))
    device = MyDevice('test', config)
    
    
    #device.temperature
    device.get_node('temperature')
    assert device.temperature.get() == 22.0
    assert device.changedstatic.get() == 19
    #assert list(device.nodes) == [device.temperature, device.humidity, device.changedstatic, device.purestatic]    
    device.nodes
    assert device.humidity.get() == 54.0
    assert device.purestatic.get() == 9
    
    assert device.changedstatic.get() == 19
    assert device.plus.get() == 19 
    assert device.stat.status is device.stat.status
    
    stat = device.stat
    assert stat is device.get_interface('stat')
    
    #stat = device.get_interface('stat')
    #print(stat.config)
    
    assert stat.get_node('status').get() == 10
    assert stat.status.get() == 10
    assert config.interface_map['stat'].node_map['status'] is device.stat.status.config
    assert device.cfg.alpha.get() == 9
    assert device.ctrl.go.get() == True
    assert device.ctrl2.go.get() == True
    assert device.ctrl.config.description == "This is something"
    assert device.ctrl2.config.description == "This is something else"
    
    device.echo.call("un", 2, "trois")
    device.echo2.call("un", 2, "trois")
    #assert device.interfaces == []
    device.hundred.get() == device.purestatic.get()*100
    device.fifty.get() == device.purestatic.get()*50
    device.fifty2.get() == device.temperature.get()*50
    
    assert device.hundred.config is device.config.node_map['hundred']
    
    assert device.purestatic.config is not MyDevice.purestatic._config
    
    assert device.fifty.config.dummy == 2
    assert device.config.node_map['fifty'] is device.fifty.config
    print('test_device', 'OK')

if __name__ == "__main__":
    test_main()
