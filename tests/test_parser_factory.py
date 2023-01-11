from pydevmgr_core import nodes
from valueparser import ParserFactory, parser




def test_various_parser_factory_inputs():

    p = ParserFactory("Clipped", min=0, max=10).build(None)
    assert p.parse(12) == 10
    
    p = ParserFactory( ("Clipped", str), min=0, max=10).build(None)
    assert p.parse(8) == "8"
    assert p.parse(12.0) == "10.0"
    
    # p = ParserFactory( dict(type="Clipped", min=0, max=10)).build(None)
    # assert p.parse(12) == 10
    
    # p = ParserFactory( parser("Clipped", min=0, max=10) ).build(None)
    # assert p.parse(12) == 10
 
def test_parse_obj_method_of_parser_factory():

    p = ParserFactory.parse_obj( dict(type="Clipped", min=0, max=10) ).build(None)
    assert p.parse(12) == 10

    p = ParserFactory.parse_obj( "Clipped")

 

def test_parser_factory_can_be_copied():
    f = ParserFactory( ("Clipped", str), min=0, max=10)
    fc = f.copy()
    assert fc.max == 10.0
    fc = f.copy(deep=True)
    assert fc.max == 10.0


def test_parser_in_node():
    v = nodes.Value( parser=dict(type="Clipped", min=0, max=10), value=5)
    assert v.get() == 5
    v.set(16)
    assert v.get() == 10.0
    
