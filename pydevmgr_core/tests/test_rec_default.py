from pydevmgr_core import Defaults

from pydevmgr_core import BaseDevice, BaseInterface, BaseNode




class N(BaseNode.Config):
    suffix: str = ""
    num: int = 0

class I(BaseInterface.Config):

    node1 : Defaults[N] = N(suffix="node1")
    node2 : Defaults[N] = N(suffix="node2")
    node3 : Defaults[N] = N(suffix="node3")


class D(BaseDevice.Config):
    stat: Defaults[I] = I()
    cfg:  Defaults[I] = I()



def test_main():
    d = D( stat={'node1': {'num':1}} )
    assert d.stat.node1.num == 1
    assert d.stat.node1.suffix == "node1"



if __name__ == "__main__":
    test_main()
