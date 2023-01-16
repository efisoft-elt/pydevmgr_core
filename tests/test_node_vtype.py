from typing import Type
from pydevmgr_core.base.vtype import  nodetype, nodedefault, VType
from pydevmgr_core import BaseNode  
def test_getting_vtype_from_default_class():
    
    assert nodetype(BaseNode) is None
    assert nodedefault(BaseNode) is None 
    assert nodetype(BaseNode.Config) is None
    assert nodedefault(BaseNode.Config) is None 

def test_getting_vtype_from_redefined_class():
    class N(BaseNode):
        class Config:
            vtype: VType = float 
    assert nodetype(N) is float
    assert nodedefault(N) == 0.0 
    assert nodetype(N.Config) is float
    assert nodedefault(N.Config) == 0.0 

def test_getting_vtype_from_instance_class():
    class N(BaseNode):
        class Config:
            vtype: VType = float 

    assert nodetype(N(vtype=int)) is int 
    assert nodetype(N.Config(vtype=int)) is int 
    
    assert nodedefault(N(vtype=(float,99.99))) == 99.99
    assert nodetype(N(vtype=(float, 99.99))) is float 
    
