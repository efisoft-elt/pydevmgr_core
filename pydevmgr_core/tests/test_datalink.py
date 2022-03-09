from pydevmgr_core import * 
from pydantic import Field 

class D(BaseDevice):
    #r = NoiseNode.prop('r', distribution="random", scale=0.8, mean=0.4)
    r = StaticNode('r', value=0.4)
    @NodeAlias1.prop('r2', node='r')
    def r2(self, value):
        return round(value, 2)
        
    posname = PosNameNode.prop('posname', node='r', poses={'A':0.2, 'B':0.4, 'C':0.6}, tol=0.2)
        
class Data(BaseDevice.Data):
    q : NodeVar[list] = Field([], node=DequeNode1.prop('q', node='r2'))
    rbis : NodeVar[float] = Field(0.0, node='r2')
    r : NodeVar[float] = 0.0
    r2 : NodeVar[float] = 0.0
    posname : NodeVar[list] = Field([], node=DequeNode1.prop('posname_list', node='posname'))


def test_main():
    
    data = Data()
    dev = D('d')
    
    dl = DataLink(dev, data)
    
    dl.download()
    dl.download()
    dl.download()
    
    dl.reset()
    
    dl.download()
    dl.download()
    dl.download()
    
    print(data)

if __name__ == "__main__":
    test_main()
