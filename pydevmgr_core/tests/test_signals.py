import pytest 
from pydevmgr_core import signals

def test_MaxIteration_signal():
    s = signals.MaxIteration(2)
    assert s()
    assert s()
    assert not s()
    assert not s()


def test_during():

    s = signals.During(0.2)
    while s():
        pass
    assert not s()

def test_timeout():

    s = signals.Timeout(0.2)
    while not s():
        pass
    assert s()


