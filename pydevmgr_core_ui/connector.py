from pydevmgr_core import (BaseConnector, ConnectorGroup, Connection, ConnectionGroup , 
        record_connector, get_connector_class)



# from dataclasses import dataclass, field
# from typing import Any, Iterable, Type


# class BaseConnector:
#     def connect(self, container: Any, obj: Any):
#         raise NotImplementedError

#     def disconnect(self, container):
#         raise NotImplementedError("disconnect")

# @dataclass
# class ConnectorGroup:
#     connectors: Iterable[BaseConnector] = field(default_factory=list)
    
#     def connect(self, container: Any, obj: Any):
#         for connector in self.connectors:
#             connector.connect(container, obj)
    
#     def disconnect(self, container: Any):
#         for connector in self.connectors:
#             connector.disconnect(container)



# class Connection:
#     def __init__(self, connector: BaseConnector,  container: Any, obj: Any):
#         self.connector = connector 
#         self.container = container
#         connector.connect(container, obj) 

#     def disconnect(self):
#         self.connector.disconnect(self.container) 
    


# connector_loockup = {}
# def record_connector( widget_type: str, python_type: Type):
#     key_loockup = ( widget_type, python_type)
#     def record(cls):
#         connector_loockup[key_loockup] = cls
#         return cls
#     return record 

# def get_connector_class( widget_type: str, python_type: Type):
#     try:
#         return connector_loockup[ ( widget_type, python_type) ] 
#     except KeyError:
#         raise ValueError( f"cannot found connector for {widget_type} for a {python_type}")
    



