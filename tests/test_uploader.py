from pydantic.main import BaseModel
import pytest
from pydevmgr_core.base.datamodel import DataLink
from pydevmgr_core.base.model_var import NodeVar
from pydevmgr_core.base.upload  import  Uploader, upload

from pydevmgr_core.nodes import Value 
from pydevmgr_core import BaseDevice , BaseNode, nodealias


class Error(BaseNode):
    def fget(self):
        raise ValueError()
    def fset(self, c):
        raise ValueError()

class Device(BaseDevice):

    v1 = Value.Config(value=1)
    v2 = Value.Config(value=2)
    
    error = Error.Config()    
        

def test_upload_some_values():
    dev = Device()
    upload( {dev.v1:10 , dev.v2:20})
    assert dev.v1.get() == 10.0 
    assert dev.v2.get() == 20.0 
    
def test_upload_data_link():
    class Data(BaseModel):
        v1: NodeVar[float] = 0.0 
        v2: NodeVar[float] = 0.0 
    data = Data(v1=10.0, v2=20.0)
    dev = Device()
    dl = DataLink(dev, data) 
    uploader = Uploader(dl)
    uploader.upload()
 
    assert dev.v1.get() == 10.0 
    assert dev.v2.get() == 20.0 
    data.v2 = 40.0
    uploader.upload()
    assert dev.v2.get() == 40.0 



def test_upload_after_adding_dl():
    class Data(BaseModel):
        v1: NodeVar[float] = 0.0 
        v2: NodeVar[float] = 0.0 
    data = Data(v1=10.0, v2=20.0)
    dev = Device()
    dl = DataLink(dev, data) 
    uploader = Uploader({})
    c = uploader.new_connection()
    c.add_datalink( dl) 
    
    uploader.upload()
    assert dev.v1.get() == 10.0 
    assert dev.v2.get() == 20.0 
    data.v2 = 40.0
    uploader.upload()
    assert dev.v2.get() == 40.0





callback_flag = False
def test_upload_callback():
    global callback_flag
    callback_flag = False 

    dev = Device()
    uploader = Uploader({dev.v1:10})
    def callback():
        global callback_flag
        callback_flag = True 
    
    c = uploader.new_connection()
    c.add_callback( callback)
    uploader.upload()
    assert callback_flag

def test_upload_failure_callback():
    global callback_flag
    callback_flag = False 

    dev = Device()
    uploader = Uploader({dev.v1:10, dev.error:1})
    def callback(er):
        global callback_flag
        callback_flag = True 
    with pytest.raises(ValueError):
        uploader.upload() 

    c = uploader.new_connection()

    c.add_failure_callback( callback)
    uploader.upload()
    assert callback_flag

    callback_flag = False 
    c.remove_failure_callback(callback)
    with pytest.raises(ValueError):
        uploader.upload() 


def test_remove_node():
    dev = Device()

    uploader = Uploader( {dev.v1:10} )

    uploader.remove_node( dev.v1)
    uploader.upload()
    assert dev.v1.get() == 1


def test_disconnect():
    dev = Device()

    uploader = Uploader({})
    c = uploader.new_connection() 

    c.add_node(dev.v1, 10)
    uploader.upload()
    assert dev.v1.get() == 10
    dev.v1.set(20)
    uploader.upload()
    assert dev.v1.get() == 10 
    c.disconnect(  ) 
    dev.v1.set(20)
    uploader.upload()
    assert dev.v1.get() == 20 

def test_connection():
    dev = Device()
    class Data(BaseModel):
        v1: NodeVar[float] = 0.0 
        v2: NodeVar[float] = 0.0 
    data = Data(v1=10.0, v2=20.0)

    uploader = Uploader()
    connection = uploader.new_connection()
    dl = DataLink( dev, data)

    connection.add_datalink(dl)
    uploader.upload()
    assert dev.v1.get() == 10.0 
    assert dev.v2.get() == 20.0 
    
    data.v1 = 100.0
    data.v2 = 200.0
    
    uploader.upload()
    assert dev.v1.get() == 100.0 
    assert dev.v2.get() == 200.0 

    connection.disconnect()
    data.v1 = 1.0
    data.v2 = 2.0 
    uploader.upload()
    assert dev.v1.get() == 100.0 
    assert dev.v2.get() == 200.0 
test_connection()


def test_sub_connection():
    dev = Device()
    class Data(BaseModel):
        v1: NodeVar[float] = 0.0 
        v2: NodeVar[float] = 0.0 
    data = Data(v1=10.0, v2=20.0)
    uploader = Uploader()

    master_connection = uploader.new_connection()
    connection = master_connection.new_connection()

    dl = DataLink( dev, data)
    connection.add_datalink(dl)
    uploader.upload()
    assert dev.v1.get() == 10.0 
    assert dev.v2.get() == 20.0 
    
    data.v1 = 100.0
    data.v2 = 200.0
    
    uploader.upload()
    assert dev.v1.get() == 100.0 
    assert dev.v2.get() == 200.0 

    master_connection.disconnect()
    data.v1 = 1.0
    data.v2 = 2.0 
    uploader.upload()
    assert dev.v1.get() == 100.0 
    assert dev.v2.get() == 200.0 


