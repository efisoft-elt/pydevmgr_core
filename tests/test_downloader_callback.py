from pydevmgr_core import Downloader 

counter = 0
def test_add_a_function_callback():
    global counter 
    counter = 0 
    d = Downloader()
    
    def f():
        global counter 
        counter += 1
    

    d.add_callback(...,  f) 

    d.download()
    assert counter == 1
    d.download()
    assert counter == 2
    d.remove_callback(..., f) 
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

    d.add_callback(..., g, priority=99)
    d.add_callback(..., f, priority=1)
    
    d.download()
    assert counter == 2

    c = d.new_connection() 
    
    def h():
        global counter 
        counter = 3 
    c.add_callback( h, priority=9999)
    d.download()
    assert counter == 3
