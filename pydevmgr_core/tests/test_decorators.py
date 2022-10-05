
from pydevmgr_core.decorators import getter, setter, finaliser, nodealias, node_maker , nodealias_maker
from pydevmgr_core import BaseNode, BaseDevice, BaseInterface, NodeAlias



def test_decorator_api():
    class I(BaseInterface):
        ...

    class D(BaseDevice):
        _toto = 0 
        
        @getter( BaseNode.Config() )
        def n(self):
            return self 
        
        @getter( BaseNode.Config() )
        def n2(self):
            return self._toto

        @setter( n2)
        def n2(self, value):
            self._toto = value

        @getter( BaseNode.Config(), include_object=True )
        def n3(self, obj):
            return obj

        @getter(BaseNode)
        def n4(self):
            return 8
        
        @getter(BaseNode)
        def n5(self):
            return 9


        @getter(NodeAlias.Config(nodes=["n4", "n5"]))
        def a1(self, n4, n5):
            return n4 + n5
         
        @nodealias("n4", "n5")
        def a2(self, n4, n5):
            return n4 * n5

        @finaliser(I)
        def i(self, i):
            i.toto = 9 
        
        

    d = D()
    assert d.n.get() is d
    assert d.n2.get() == 0 
    d.n2.set( 99) 
    assert d.n2.get() == 99 
    assert isinstance(d.n3.get(), BaseNode)

    assert d.n4.get() == 8    
    assert d.i.toto == 9
    assert d.a1.get() == d.n4.get()+d.n5.get()
    assert d.a2.get() == d.n4.get()*d.n5.get()


def test_node_maker():

    @node_maker()
    def n():
        return 2 

    assert n.get() == 2
    assert n.key == "n"

    @node_maker(value=( float, 3.0), include_object=True)
    def n2(self):
        return self.value

    assert n2.get() == 3.0

    @nodealias_maker(n, scale = 10.0, include_object=True)
    def scaled(self, n):
        return n * self.scale 

    assert scaled.get() == 20.0
     
