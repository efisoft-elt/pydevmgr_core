from valueparser.parsers import Clipped
from pydevmgr_core import BaseRpc
from pydevmgr_core.base.rpc import Arg 
from valueparser import parser


def test_arg_are_parsed():

    rpc = BaseRpc( args=[Arg.Config(name="pos", parser=float), Arg.Config(name="vel", parser=float)])
    assert rpc.args[0].parse("1.0") == 1.0

    rpc = BaseRpc( args=[{"name":"pos", "parser":float}])
    assert rpc.args[0].parse("1.0") == 1.0

def test_arg_legacy():
    rpc = BaseRpc( arg_parsers=[float])
    assert rpc.args[0].parse(1.0) == 1.0


arg1, arg2 = None, None 

def test_rpc_arg():
    
    class Rpc(BaseRpc):
        def fcall(self, a1, a2):
            global arg1, arg2 
            arg1 = a1 
            arg2 = a2 
            return 0 
    
    c = parser( (float, Clipped), max=1.0)

    rpc = Rpc( args=[Arg.Config(name="a1", parser=float), Arg.Config(name="a2", parser=c)])
    rpc.call( 10, "20")

    assert arg1 == 10 
    assert arg2 == 1.0
            

