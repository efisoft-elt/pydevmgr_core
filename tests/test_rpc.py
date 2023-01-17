import pytest 
from pydevmgr_core import BaseRpc, KINDS 
from pydevmgr_core import parsers

def test_rpc_api():
    
    rpc = BaseRpc('test')
    
    assert rpc.key == 'test'
    assert rpc.name == 'test'
    assert rpc.sid == 0

    
    class MyRpc(BaseRpc):
        def fcall(self, arg1, arg2):
            return arg1+arg2
        
    myrpc = MyRpc('test', args=[{"name":"a1", "parser":int}, {"name":"a2", "parser":int}])
    
    assert myrpc.call(0, 0) is 0

    assert myrpc.call(0, 0.2) is 0
    assert myrpc.call(1, 10) is 11
    assert myrpc.call("1", "10") is 11

    with pytest.raises(RuntimeError):
        myrpc.rcall(1,1)

    myrpc = MyRpc('test', args=[{"name":"a1","parser":int}, {"name":"a2", "parser":{'type':("int","Clipped"), 'min':0}}])
      
    assert myrpc.call(1, -1) == 1

