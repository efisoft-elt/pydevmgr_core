from pydantic.dataclasses import dataclass
from pydantic.main import BaseModel, Field
import pytest
from pydevmgr_core import DataLink, BaseDevice, BaseInterface
from systemy import FactoryDict
from pydevmgr_core.base.model_var import NodeVar, NodeVar_R, NodeVar_RW, NodeVar_W, StaticVar
from pydevmgr_core.base.node_alias import NodeAlias1
from pydevmgr_core.nodes import Value

from pydevmgr_core.base.datamodel import NodeField, NodeMode, NodeResolver, NormalClassExtractor, ObjField, PydanticModelExtractor, SingleNodeModelExtractor, SingleNodeNormalClassExtractor, StaticField, create_model_info, get_annotations

class Scale(NodeAlias1):
    class Config:
        scale: float = 1.0
    
    def fget(self, value):
        return value* self.scale 

class Device(BaseDevice):
    class BaseInterface(BaseInterface):
        i1 = Value.Config(value="i1")
        i2 = Value.Config(value="i2")
    
    i = BaseInterface()
    
    n1 = Value.Config(value="n1")
    n2 = Value.Config(value="n2")
    x = Value.Config(value=1)

    d = FactoryDict( {"node1": Value.Config(value="node1")})

# field extractor 


def test_model_field_resolver():
    
    class M(BaseModel):
        n1 : NodeVar_W = ""
        n2: NodeVar_R = ""
        i1: NodeVar = Field("", node="i.i1")
        i2: NodeVar = Field("", node=("i", "i2"))
        
        node: NodeVar = Field(0, node=Value(value=99))
        factory: NodeVar = Field(0, node=Scale.Config( node="x", scale=10)) 

        bad: NodeVar = 0.0 
        key: StaticVar = ""

        class Interface(BaseModel):
            i1: NodeVar = ""
            i2: NodeVar = ""
        i = Interface()
        
        
    dev = Device()
    
    f = NodeField.from_field( "n1", M.__fields__["n1"]) 
    assert f.mode == NodeMode.W 
    assert f.resolve(dev) == dev.n1

    f = NodeField.from_field( "n2", M.__fields__["n2"]) 
    assert f.mode == NodeMode.R 
    assert f.resolve(dev) == dev.n2

    f = NodeField.from_field( "i1", M.__fields__["i1"]) 
    assert f.mode == NodeMode.RW
    assert f.resolve(dev) == dev.i.i1

    f = NodeField.from_field( "i2", M.__fields__["i2"]) 
    assert f.mode == NodeMode.RW
    assert f.resolve(dev) == dev.i.i2

    f = NodeField.from_field( "node", M.__fields__["node"]) 
    assert f.resolve(dev).get() == 99
    
    f = NodeField.from_field( "factory", M.__fields__["factory"]) 
    assert f.resolve(dev).get() == 10
    
    f = NodeField.from_field( "bad", M.__fields__["bad"])
    with pytest.raises(AttributeError):
        f.resolve(dev)
    
    f = StaticField.from_field( "key", M.__fields__["key"])
    assert f.resolve(dev) == dev.key
    
    f = ObjField.from_field("i", M.__fields__["i"])
    assert f.resolve(dev) == dev.i  
    
    with pytest.raises(ValueError):
        f = ObjField.from_field("key", M.__fields__["key"])
        f.resolve(dev)
    



def test_normal_class_resolver():

    class Data:
        n1: NodeVar = ""
        n2: NodeVar[str] = ""
        key: StaticVar[str] = "" 
        class Interface(BaseModel):
            i1: NodeVar = ""
            i2: NodeVar = ""
        i = Interface()

    dev = Device() 

    f = NodeField.from_member( "n1", NodeVar)
    assert f.resolve(dev) == dev.n1 
    f = NodeField.from_member( "n2", NodeVar)
    assert f.resolve(dev) == dev.n2 
    f = StaticField.from_member( "key",StaticVar)
    assert f.resolve(dev) == dev.key
    
    f = ObjField.from_member("i", None)
    assert f.resolve(dev) == dev.i 



def test_model_extractor_resolver():
    class Data(BaseModel):
        n1: NodeVar = ""
        n2: NodeVar[str] = ""
        class I(BaseModel):
            i1: NodeVar_R = ""
        i = I()
    dev = Device() 
    data = Data() 
    fields = PydanticModelExtractor().extract(Data) 
    nodes = NodeResolver( PydanticModelExtractor() ).resolve(fields,dev, data)
    assert len(nodes.readable_nodes) == 3
    assert len(nodes.writable_nodes) == 2

def test_normal_class_extractor_resolver():
    class Data:
        n1: NodeVar = ""
        n2: NodeVar[str] = ""
        class I:
            i1: NodeVar_R = ""
        i = I()
    dev = Device() 
    data = Data()
    extractor = NormalClassExtractor() 
    
    fields = extractor.extract(Data) 
    nodes = NodeResolver(extractor ).resolve(fields,dev, data)
    assert len(nodes.readable_nodes) == 3
    assert len(nodes.writable_nodes) == 2


def test_single_node_model_extraction():
    class Data(BaseModel):
        value: str = ""
    
    n = Value(value=10) 
    d= Data() 

    extractor = SingleNodeModelExtractor()
    fields = extractor.extract(Data)
    resolver = NodeResolver( extractor) 
    nodes = resolver.resolve( fields, n , d) 
    assert nodes.readable_nodes[n][0] == ("value", d) 

def test_single_node_normal_class_extraction():
    class Data:
        value: str = ""
    
    n = Value(value=10) 
    d= Data() 

    extractor = SingleNodeNormalClassExtractor()
    fields = extractor.extract(Data)
    resolver = NodeResolver( extractor) 
    nodes = resolver.resolve( fields, n , d) 
    assert nodes.readable_nodes[n][0] == ("value", d) 


#  # # # # # # # # #  # # # # # # # # # ### 
 





def test_datalink_with_base_model():

    class Data(BaseModel):
        class Interface(BaseModel):
            i1: NodeVar[str] = ""
            i2: NodeVar = ""
        i = Interface()
        
        n1: NodeVar[str] = ""
        n2: NodeVar = ""

    dev = Device()
    data = Data()
    dl = DataLink( dev, data)
    dl.download()

    assert data.i.i1 == dev.i.i1.get()

    assert data.i.i2 == dev.i.i2.get()

    assert data.n1 == dev.n1.get()
    assert data.n2 == dev.n2.get()



def test_datalink_field_path():
   
    class SData(BaseModel):
        n1: NodeVar = ""
        n2: NodeVar = ""

    class Data(BaseModel):

        n1: NodeVar = ""
        n2: NodeVar = Field("", node="n2")

        dn1: NodeVar = Field("", node="d['node1']")
        i1: NodeVar[str] = Field("", node="i.i1")
        

        class Interface(BaseModel):
            i1: NodeVar[str] = ""
            i2: NodeVar = ""
        ii = Field(Interface(), path="i")
        self =  Field(SData(), path=".") 
        

    dev = Device()
    data = Data()
    dl = DataLink( dev, data) 
    dl.download()
    
    assert data.n1 == dev.n1.get()
    assert data.dn1 == dev.d['node1'].get()
    assert data.i1 == dev.i.i1.get()

    assert data.ii.i1 == dev.i.i1.get()
    assert data.self.n1 == dev.n1.get()

    
def test_link_several_model():

    class D1:
        n1 : NodeVar = ""
    class D2:
        n2: NodeVar = "" 

    d1, d2 = D1(), D2()
    dev = Device()
    dl = DataLink( dev, d1, d2)
    dl.download()
    
    assert d1.n1 == dev.n1.get()
    assert d2.n2 == dev.n2.get()


def test_link_a_node():
    @dataclass
    class Data:
        value = 0.0
    
    d = Data()
    dev = Device()
    dl = DataLink(dev.x, d) 
    dl.download()
    assert d.value == dev.x.get()
    
def test_link_a_node_to_a_data():
    class ValueData:
        value = 0.0 

    class Data:
        x: NodeVar = ValueData()

    d = Data()
    dev = Device()
    dl = DataLink(dev, d)
    dl.download()
    assert d.x.value == dev.x.get()


def test_info_extractor():
    class Info(BaseModel):
        unit: str = ""
        description: str = ""
    
    class Data(BaseModel):
        x: float = Field(0.0, unit="mm", description="This is x")
        
        class SubData(BaseModel):
            t: float = Field(0.0, unit="time", description="This is t")
        sub = SubData()
        
  
    InfoData = create_model_info( Data, Info)  
    i = InfoData()
    
    assert i.x.unit == "mm"
    assert i.x.description == "This is x"
    assert i.sub.t.unit == "time" 


def test_info_extractor_with_filter():
    class Info(BaseModel):
        unit: str = ""
        description: str = ""
    
    class Data(BaseModel):
        x: float = Field(0.0, unit="mm", description="This is x")
        text: str = "" 

        
  
    InfoData = create_model_info( Data, Info, include_type=float)  
    i = InfoData()
    
    assert i.x.unit == "mm"
    assert i.x.description == "This is x"
    with pytest.raises(AttributeError):
        i.text
    
    InfoData = create_model_info( Data, Info, include_type=(float, str))  
    i = InfoData()
    
    assert i.x.unit == "mm"
    assert i.x.description == "This is x"
    assert i.text.unit == ""

    InfoData = create_model_info( Data, Info, include={"x"})  
    i = InfoData()
    
    assert i.x.unit == "mm"
    with pytest.raises(AttributeError):
        i.text

    InfoData = create_model_info( Data, Info, exclude={"text"})  
    i = InfoData()
    
    assert i.x.unit == "mm"
    with pytest.raises(AttributeError):
        i.text
    
    InfoData = create_model_info( Data, Info, exclude_type=str)  
    i = InfoData()
    
    assert i.x.unit == "mm"
    with pytest.raises(AttributeError):
        i.text

