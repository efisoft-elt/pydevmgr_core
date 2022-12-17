import pytest
from pydevmgr_core import BaseMonitor, BaseDevice, nodes, NodeVar, DataLink, signals


# class Device(BaseDevice):

#     node1 = nodes.Value.Config( value=10.0) 
#     node2 = nodes.Value.Config( value=20.0) 

# class Monitor(BaseMonitor):
     
#     class Config:
        
#         value1: float = 9.99
#         value2: float = 9.99

    
#     class Data(BaseMonitor.Data):
#         node1: NodeVar[float] = 0.0
#         node2: NodeVar[float] = 0.0



# def test_data_creation_and_link():
#     s = Monitor()
#     dev = Device()
#     data = s.Data()
        
#     dl = DataLink(dev, data)  
#     assert data.node1 == 0.0 
#     dl.download()
#     assert data.node1 == 10.0

# def test_update():
#     s = Monitor()
#     dev = Device()
#     data = s.Data()
    
#     dl = DataLink(dev, data)
#     dl.download()
    
#     with pytest.raises( Monitor.NextSetup ):
#         s.update(data) 

# def test_start():
#     s = Monitor()
#     dev = Device()
#     data = s.Data()

#     s.start(dev, data)


# def test_end():
#     s = Monitor()
#     dev = Device()
    
#     data = s.Data()
#     s.end(dev, data, None)


# def test_next():
#     s = Monitor()
#     device = Device()
#     data = Monitor.Data()
     

#     s.next(device, data)
#     s.next( device, data )

