from pydevmgr_core import * 


class D(BaseDevice):
    my_node = StaticNode.prop('my_node', value=99)
    @NodeAlias.prop('my_alias', nodes=['my_node'])
    def my_dev_alias(self, my_node_value):
        return my_node_value * 10

class D2(BaseDevice):
    d2_node = StaticNode.prop('d2_node', value=78)
    
class I(BaseInterface):
    _devices = []
    
    @BaseNode.prop('all_my_node')
    def all_my_node(self):
        return download([d.my_node  for d in  self._devices])
    
    static = StaticNode.prop('static', value=56)
    

class M(BaseManager):
    d = D.prop('d')
    @NodeAlias.prop('my_alias', nodes=[('d','my_node')])
    def my_alias(self, my_node_value):
        return my_node_value * 10
    
    @I.prop('stat')
    def stat(self, stat):        
        stat._devices = list(self.devices)

class R(BaseRpc):
    class Config(BaseRpc.Config):
        offset: float = 0.0
    def fcall(self):
        print(f"RPC called with offset {self.config.offset}")
        return self.config.offset

    
y = """
node_map: 
    my_dynamic_alias: 
        type: Formula1
        node: my_alias 
        formula: x*10
    my_dynamic_alias2:
        type: Formula
        nodes: [['d','my_node']]
        formula: x*10
"""

    
def test_main():
    global y 
    #m = M(node_map=dynamic_nodes)
    m = M(config=io.load_yaml(y))
    assert m.my_dynamic_alias.get() == 99*10*10   
    assert m.my_dynamic_alias2.get() == 99*10 
    assert m.stat.all_my_node.get() == [99]
    assert D.new(m, None, m.config.device_map['d']).config is m.d.config
    
    m.add_device(None,  D2('d2'))
    assert m.d2.d2_node.get() == 78
    assert m.d2 in list(m.devices)
    
    m._clear_all()
    #assert m.d2 in list(m.devices)
    assert m.d2.d2_node.get() == 78
    
    m.d2.add_node('n10', StaticNode(value=67) )
    assert m.d2.n10.get() == 67
    
    m.d2.add_interface('i10', I())
    m.d2.i10.static.get() == 56
    
    m.d2.i10.add_rpc('move', R())
    assert m.d2.i10.move.call() == 0 
    m.d2.i10.config.rpc_map['move'].offset = 90
    assert m.d2.i10.move.call() == 90
    
    m.add_device( 'd3', {'type':'Base', 'node_map':{'a':{'type':'Static','value':84}}})
    
    
    assert m.d3.a.get() == 84
    d3 = m.d3
    assert d3 in m.devices
    m.remove_device('d3')
    assert d3 not in m.devices
    
    
if __name__ == "__main__":
    test_main()   
