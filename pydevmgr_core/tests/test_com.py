from pydevmgr_core.base.com import BaseCom 


def test_com_api():

    com = BaseCom()
    assert com.localdata == {}

def test_com_childinng():
    parent = BaseCom()
    child = BaseCom.new(parent, None)
    assert child.localdata is parent.localdata
