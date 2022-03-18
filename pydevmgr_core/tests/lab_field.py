from pydevmgr_core import BaseNode, BaseDevice , BaseInterface, record_class, get_class, NodeAlias, PolynomNode1, _BaseObject
from typing import Dict 


@record_class
class N(BaseNode):
    class Config(BaseNode.Config):
        type = "N"
        num: int  = 0

        
        @classmethod
        def validate_type(cls, type):
            if type:
                if type not in  ["N", "NN"]:
                    raise ValueError(f"Expecting a node of type N got a {type}")
            return type 


    def fget(self):
        return self.config.num 


@record_class
class NN(N):
    class Config(N.Config):
        type = "NN"
        num: int  = 0


@record_class
class D(BaseInterface):
    class Config(BaseInterface.Config):
        type = "D"
        n : N.Config = N.Config()   
        nn : NN.Config = NN.Config()

        nodes: Dict[str, N.Config] = {
                'n_d1' : N.Config(num=12)    
            }
        auto_build = True

        n_c = PolynomNode1.Config( polynom=[10, 2], node="n" )

    nodes = BaseNode.Dict.prop('nodes')

class I(BaseInterface):
    class Config(BaseInterface.Config):
        type = "I"
        toto: BaseNode.Config = N.Config()
        d: D.Config = D.Config()
        auto_build = True
   
    toto = BaseNode.prop()
   
d = D("d", n = {"type":'N', 'num':2},  nodes = {'n1': {"num":1, "type":"N"}, 'n2': {}}, auto_build=True )

# print (d.config)
# d = D(n = {"type": "NN"})

assert d.nn is d.nn
assert d.n_c.get() == 14
N.Config(num=8)

# print( list(d.find(BaseNode) )) 
i = I("i", auto_build=True)

print(  list(d.nodes.values()) )

print( list(i.find(_BaseObject, -1) ))

print(i.toto)
