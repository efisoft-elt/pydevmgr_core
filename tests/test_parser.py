from pydevmgr_core import parsers

from valueparser import conparser
import pytest 
from enum import Enum 
from pydantic import BaseModel


def test_conpraser():
    class Model(BaseModel):
        number: conparser(int) = 0
        pos : conparser( (float, parsers.Clipped), min=0.0, max=1.0) = 0.5

    m = Model(pos=2.0, number=1.2)
    assert m.number == 1 
    assert m.pos == 1.0


def test_clipped():
    p = parsers.Clipped(min=0, max=10)
    assert p.parse(1) == 1
    assert p.parse(0) == 0
    assert p.parse(-1) == 0
    assert p.parse(10) == 10
    assert p.parse(11) == 10

def test_bounded():
    p = parsers.Bounded(min=0, max=10)
    assert p.parse(0) == 0
    assert p.parse(1) == 1
    assert p.parse(10) == 10
    with pytest.raises( ValueError):
        p.parse(11)
    with pytest.raises( ValueError ):
        p.parse(-1)
    p = parsers.Bounded()
    assert p.parse(-1e4) == -1e4
    assert p.parse(1e45) == 1e45

def test_loockup():
    p = parsers.Loockup(loockup=["A", "B", 2, 3])
    assert p.parse("A") == "A"
    assert p.parse(2) == 2
    
    with pytest.raises( ValueError ):
        p.parse("Not In loockup") 
    
    p = parsers.Loockup()
    with pytest.raises( ValueError ):
        p.parse(5)

def test_enumerated():

    class E(int, Enum):
        UN = 1
        DEUX = 2
        TROIS = 3

    p = parsers.Enumerated( enumerator = E )
    assert p.parse(1) == 1
    assert p.parse(E.UN) == E.UN 
    assert p.parse(E.UN) == 1
    assert p.parse(E.TROIS) == 3
    
    with pytest.raises( ValueError ):
        p.parse(6)


def test_rounded():
    p = parsers.Rounded( ndigits=2 )
    assert p.parse(3.2345) == 3.23 
    assert p.parse(6.7887236) == 6.79
    assert p.parse(0.0) == 0.0
 

def test_tostring():
    p = parsers.ToString(format="%.1f")
    assert p.parse(3.4564) == "3.5"
    assert p.parse(1) == "1.0"
     
def test_capitalized():
    p = parsers.Capitalized()
    
    assert p.parse("this_is") == "This_is"
    assert p.parse("mixedCap") == "Mixedcap"
    assert p.parse("") == ""
    
def test_stripped():
    p = parsers.Stripped( strip="-")
    
    assert p.parse("-----abc") == "abc"
    assert p.parse("----abc-") == "abc"
    assert p.parse("--abc") == "abc"

    p = parsers.Stripped( )
    assert p.parse("   abc  ") == "abc"
    
def test_lstripped():
    p = parsers.LStripped( lstrip="-")
    
    assert p.parse("-----abc") == "abc"
    assert p.parse("----abc-") == "abc-"
    assert p.parse("-abc") == "abc"

    p = parsers.LStripped( )
    assert p.parse("   abc  ") == "abc  "

def test_rstripped():
    p = parsers.RStripped( rstrip="-")
    
    assert p.parse("--abc") == "--abc"
    assert p.parse("----abc-") == "----abc"
    assert p.parse("-abc") == "-abc"

    p = parsers.RStripped( )
    assert p.parse("   abc  ") == "   abc"

def test_formula():
    
    p = parsers.Formula( formula="2*x+10")
    assert p.parse(3) == 16
    with pytest.raises(TypeError):
        p.parse("a") 
    
    p = parsers.Formula() 
    assert p.parse(4.5) == 4.5
    
    p = parsers.Formula( formula="10*a", varname="a")
    assert p.parse(3.0) == 30
    
    p = parsers.Formula( formula="exp(x)")
    assert p.parse(0.0) == 1.0
