
from pydevmgr_core import BaseNode, BaseDevice, record_class

@record_class
class N(BaseNode):
    class Config(BaseNode.Config):
        type = "N"
        num: int = 0 

class D(BaseDevice):
    class Config(BaseDevice.Config):
        nodes: dict = { 'n1': {'type':'N', 'num':9} } 
    
    nodes = BaseNode.Dict.prop('nodes', default_type="N")


d1 = D(nodes=  { 'n1': {'num':4} } )
d2 = D()
# d = D()
# d.config.nodes['n1'].num == 9 
assert d1.nodes['n1'].config.num == 4
assert d2.nodes['n1'].config.num == 9 
