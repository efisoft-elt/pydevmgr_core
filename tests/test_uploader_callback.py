from pydevmgr_core import Uploader 

counter = 0
def test_add_a_function_callback():
    global counter 
    counter = 0 
    u = Uploader()
    
    def f():
        global counter 
        counter += 1
    

    u.add_callback(  f) 

    u.upload()
    assert counter == 1
    u.upload()
    assert counter == 2
    u.remove_callback( f) 
    u.upload()
    assert counter == 2

def test_call_back_priority():
    global counter 
    counter = 0 
    u = Uploader()
    
    def f():
        global counter 
        counter = 1 
    def g():
        global counter 
        counter = 2 

    u.add_callback( g, priority=99)
    u.add_callback( f, priority=1)
    
    u.upload()
    assert counter == 2

