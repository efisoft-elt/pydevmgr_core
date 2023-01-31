from pydevmgr_core import Downloader 
from pydevmgr_core import nodes  
counter = 0
def test_add_a_function_callback():
    global counter 
    counter = 0 
    d = Downloader()
    
    def f():
        global counter 
        counter += 1
    

    d.add_callback(  f) 

    d.download()
    assert counter == 1
    d.download()
    assert counter == 2
    d.remove_callback( f) 
    d.download()
    assert counter == 2

def test_call_back_priority():
    global counter 
    counter = 0 
    d = Downloader()
    
    def f():
        global counter 
        counter = 1 
    def g():
        global counter 
        counter = 2 
    

    d.add_callback( g, priority=99)

    d.add_callback( f, priority=1)
  
    d.download()
    assert counter == 2

    c = d.new_connection() 
    
    def h():
        global counter 
        counter = 3 
    c.add_callback( h, priority=9999)
    d.download()
    assert counter == 3


def test_download_connection():
    n1 = nodes.Value(value=1, vtype=int)
    n2 = nodes.Value(value=2, vtype=int)
    n3 = nodes.Value(value=3, vtype=int)
    
    d = Downloader()
    d.add_node( n1) 
    assert d._data[n1] == 0
    c = d.new_connection()
    c.add_node( n2 )
    assert d._data[n2] == 0
    c.download()
    assert d._data[n2] == 2
    assert d._data[n1] == 0
    
    cc = c.new_connection()
    cc.add_node( n3 )
    d._data[n2] = 0
    assert d._data[n1] == 0
    assert d._data[n2] == 0
    assert d._data[n3] == 0
    
    cc.download()
    assert d._data[n1] == 0
    assert d._data[n2] == 0
    assert d._data[n3] == 3
    
    d._data[n3] = 0
    c.download()
    assert d._data[n2] == 2
    assert d._data[n3] == 3




    d.download()
    assert d._data[n1] == 1
    assert d._data[n2] == 2
    assert d._data[n3] == 3

    cc.disconnect()
    d._data[n2] = 0
    d._data[n3] = 0
    c.download()
    assert d._data[n2] == 2
    assert d._data[n3] == 0


    
        
