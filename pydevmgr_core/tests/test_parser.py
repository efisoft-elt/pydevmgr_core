from pydevmgr_core import parser, create_parser_class, Rounded, Clipped,  Stripped, ToString
from pydevmgr_core import BaseNode, BaseRpc

def test_main():
    fr = parser((float, Rounded, Clipped), ndigits=2, max=3.0)
    fr2 = parser((float, Rounded, Clipped), dict(ndigits=2, max=3.0))
    assert fr.__class__ is fr2.__class__
    assert fr(2.3456) == 2.35
    assert fr(3.3456) == 3.0
    fr.config.max = 4
    assert fr(3.3456) == 3.35

    assert fr2.config.ndigits == 2

    FR = create_parser_class((float, Rounded, Clipped))
    fr = parser( (FR,  ToString), ndigits=2, max=3.0, format="%.2f")
    assert fr(3.3456) == '3.00'

    fr = parser( (float, ))        
    fr = parser( (Rounded, ), ndigits=0)
    assert fr(1.234)==1.0   


    fr = parser( Rounded, ndigits=0)
    assert fr(1.234)==1.0    
    fr = parser( 'Rounded', ndigits=0)
    assert fr(1.234)==1.0  
    fr = Rounded(ndigits=0)
    assert fr(1.234)==1.0  
      
    fr = parser( ('Rounded','Clipped'), ndigits=0, min=0)
    assert fr(1.234) ==1.0    
    assert fr(-1.234) == 0.0    

    fr = parser((str, Stripped))
    assert fr(' un ') == 'un'
    assert fr(1.3) == '1.3'


    n = BaseNode(parser="Clipped")
    assert n._parser.config is n.config.parser
    n.config.parser.max = 12 
    assert  n._parser.config.max  == 12

    r = BaseRpc(args_parser=["Clipped"], kwargs_parser={'toto':[float,"Clipped"] })
    assert r._args_parser[0].config is r.config.args_parser[0]
    r.config.args_parser[0].max = 10
    assert r._kwargs_parser['toto'].config is r.config.kwargs_parser['toto']

if __name__ == "__main__":
    test_main()
