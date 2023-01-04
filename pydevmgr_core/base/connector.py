from dataclasses import dataclass, InitVar, field
from typing import Any, Iterable, List, Type
from typing_extensions import Protocol

class BaseConnector(Protocol):
    """ A non symetric connection maker between two objects 

    The container (first object) can be modified to hold connection information 
    and is parsed to disconnect and refresh methods 
    """    
    def connect(self, container: Any, obj: Any) -> None:
        raise NotImplementedError("connect") 
    
    def refresh(self, container: Any):
        pass

    def disconnect(self, container: Any):
        pass
    
@dataclass
class ConnectorGroup:
    connectors: Iterable[BaseConnector] = field(default_factory=list)
    
    def connect(self, container: Any, obj: Any) -> None:
        for connector in self.connectors:
            connector.connect( container, obj)

    
    def disconnect(self, container: Any) -> None:
        for connector in self.connectors:
            connector.disconnect(container)

    def refresh(self, container: Any) -> None:
        for connector in self.connectors:
            connector.refresh(container)


@dataclass
class Connection:
    connector: BaseConnector
    container: Any 
    obj: InitVar[Any]
    
    def __post_init__(self, obj):
        self.connection_data = self.connector.connect( self.container, obj)

    def disconnect(self):
        if self.container:
            self.connector.disconnect(self.container)
            self.container = None

    def refresh(self):
        if self.container is None:
            raise RuntimeError("This connection was probably disconnected")
        self.connector.refresh(self.container)



@dataclass
class ConnectionGroup:
    connections: List[Connection] = field(default_factory=list)
    
    def disconnect(self):
        for connection in self.connections:
            connection.disconnect()

    def refresh(self):
        for connection in self.connections:
            connection.refresh()


connector_loockup = {}
def record_connector(obj1_type: Type, obj2_type: Type):
    key_loockup = (obj1_type, obj2_type)
    def record(cls):
        connector_loockup[key_loockup] = cls
        return cls
    return record 

def get_connector_class( obj1_type: Type, obj2_type: Type):
    try:
        return connector_loockup[ ( obj1_type, obj2_type) ] 
    except KeyError:
        raise ValueError( f"cannot found connector for {obj1_type} and a {obj2_type}")
    



