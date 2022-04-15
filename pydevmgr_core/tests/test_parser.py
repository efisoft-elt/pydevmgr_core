from pydevmgr_core import parsers
import pytest 
from enum import Enum 

def test_clipped():
    p = parsers.Clipped(min=0, max=10)
    assert p(1) == 1
    assert p(0) == 0
    assert p(-1) == 0
    assert p(10) == 10
    assert p(11) == 10

def test_bounded():
    p = parsers.Bounded(min=0, max=10)
    assert p(0) == 0
    assert p(1) == 1
    assert p(10) == 10
    with pytest.raises( ValueError):
        p(11)
    with pytest.raises( ValueError ):
        p(-1)
    p = parsers.Bounded()
    assert p(-1e4) == -1e4
    assert p(1e45) == 1e45

def test_loockup():
    p = parsers.Loockup(loockup=["A", "B", 2, 3])
    assert p("A") == "A"
    assert p(2) == 2
    
    with pytest.raises( ValueError ):
        p("Not In loockup") 
    
    p = parsers.Loockup()
    with pytest.raises( ValueError ):
        p(5)

def test_enumerated():

    class E(int, Enum):
        UN = 1
        DEUX = 2
        TROIS = 3

    p = parsers.Enumerated( enumerator = E )
    assert p(1) == 1
    assert p(E.UN) == E.UN 
    assert p(E.UN) == 1
    assert p(E.TROIS) == 3
    
    with pytest.raises( ValueError ):
        p(6)


def test_rounded():
    p = parsers.Rounded( ndigits=2 )
    assert p(3.2345) == 3.23 
    assert p(6.7887236) == 6.79
    assert p(0.0) == 0.0
 

def test_tostring():
    p = parsers.ToString(format="%.1f")
    assert p(3.4564) == "3.5"
    assert p(1) == "1.0"
     
def test_capitalized():
    p = parsers.Capitalized()
    
    assert p("this_is") == "This_is"
    assert p("mixedCap") == "Mixedcap"
    assert p("") == ""
    
def test_stripped():
    p = parsers.Stripped( strip="-")
    
    assert p("-----abc") == "abc"
    assert p("----abc-") == "abc"
    assert p("--abc") == "abc"

    p = parsers.Stripped( )
    assert p("   abc  ") == "abc"
    
def test_lstripped():
    p = parsers.LStripped( lstrip="-")
    
    assert p("-----abc") == "abc"
    assert p("----abc-") == "abc-"
    assert p("-abc") == "abc"

    p = parsers.LStripped( )
    assert p("   abc  ") == "abc  "

def test_rstripped():
    p = parsers.RStripped( rstrip="-")
    
    assert p("--abc") == "--abc"
    assert p("----abc-") == "----abc"
    assert p("-abc") == "-abc"

    p = parsers.RStripped( )
    assert p("   abc  ") == "   abc"

def test_formula():
    
    p = parsers.Formula( formula="2*x+10")
    assert p(3) == 16
    with pytest.raises(TypeError):
        p("a") 
    
    p = parsers.Formula() 
    assert p(4.5) == 4.5
    
    p = parsers.Formula( formula="10*a", varname="a")
    assert p(3.0) == 30
    
    p = parsers.Formula( formula="exp(x)")
    assert p(0.0) == 1.0
