from systemy.system import FactoryList
import yaml
from pydevmgr_core import BaseDevice, nodes, Alias
from pydevmgr_core.base.io import PydevmgrLoader 

    

def test_basic_alias_query():
    class Dev(BaseDevice):
        x = nodes.Value.Config(value=5)
        y = Alias("x")

    dev = Dev()
    assert dev.y is dev.x

def test_alias_in_factory_list():
    class Dev(BaseDevice):
        
        class Config:
            nodes = FactoryList[Alias]( ["n1", "n2"] )
            na: Alias = Alias("n1")

        n1 = nodes.Value.Config(value=5)
        n2 = nodes.Value.Config(value=10)
        
        na1 = Alias("nodes[1]")

    dev = Dev()
    assert dev.nodes[0] is dev.n1
    assert dev.nodes[1] is dev.n2
    
    dev = Dev( na="n2" )
    assert dev.na is dev.n2 
    
    assert dev.na1 is dev.n2 


# payload = """
# a: !factory:Alias {target: 'nodes[0]'}
# """
payload = """
a: !factory:Alias 'nodes[0]'
"""
def test_alias_in_payload():

    class Dev(BaseDevice, extra="allow"):
        class Config:
            nodes = FactoryList( [nodes.Value.Config(value=1), nodes.Value.Config(value=2)])

    dev = Dev.Config( **yaml.load( payload, PydevmgrLoader ) ).build()
    assert dev.a is dev.nodes[0]
