from pydevmgr_core import BaseDevice, BaseNode, record_class
from pydantic import BaseModel 
from typing import Dict
import yaml


cfg_txt = """---
node_map:
    temperature:        
       type: Static
       value: 22.0
    humidity:    
       type: Static
       value: 54.0
interface_map:
    cfg:
        node_map:
            alpha:
                type: Static
                value: 8.4 
"""

cfg_txt2 = """---
node_map:
    temperature:  
       type: Static
       value: 22.0
    humidity:
        type: Static       
        value: 54.0
"""


cfg_txt_er1 = """---
temperature: 22
"""


def test_main():
    config = BaseDevice.Config.parse_obj(yaml.load(cfg_txt, yaml.CLoader))
    assert config.node_map['temperature'].value == 22.0    
    assert config.interface_map['cfg'].node_map['alpha'].value == 8.4 
    
    config = BaseDevice.Config.parse_obj(yaml.load(cfg_txt2, yaml.CLoader))
    assert config.node_map['temperature'].value == 22.0
    print('test_device_config', 'OK')

if __name__ == "__main__":
    test_main()

