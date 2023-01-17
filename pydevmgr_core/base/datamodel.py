from dataclasses import dataclass, field
from enum import Enum, auto
from pydantic import BaseModel, ValidationError, Field
from pydantic.fields import ModelField
from pydantic.main import create_model

from .vtype import VType, find_vtype, nodedefault, nodetype, _vtype_type, _vtype_default
from .download import download, BaseDataLink, reset
from .upload import upload
from .node import BaseNode
from .model_var import NodeVar, NodeVar_R, NodeVar_W, NodeVar_RW, StaticVar
from .base import BaseData, BaseFactory, BaseObject
from .object_path import AttrPath, ObjPath, BasePath, TuplePath, objpath
from typing import  Any, Iterable, Dict, List, Optional, Set,  Tuple, Type, Union
from warnings import warn
import inspect
try:
    get_annotations = inspect.get_annotations
except AttributeError:
    try:
        from get_annotations import get_annotations
    except ImportError:
        # patch if get_annotations id not here 
        def get_annotations(obj):
            return obj.__annotations__

def get_fields(model: BaseModel):
    return model.__fields__


class C:
    ATTR = 'attr'
    ITEM = 'item'
    NODE = 'node'
    PATH = 'path'

class MatchError(ValueError):
    ...

class NodeMode(str, Enum):
    RW = "rw"
    R = "r"
    W = "w"

def _node_var2mode(node_var):
    if issubclass(node_var, NodeVar_W):
        return  NodeMode.W 
    if issubclass( node_var, NodeVar_R):
        return NodeMode.R 
    
    return NodeMode.RW
    


@dataclass
class NodeField:
    node: Union[ObjPath, BaseNode, BaseFactory] 
    name: str
    mode: NodeMode = NodeMode.RW 
    

    def resolve(self, obj):
        if isinstance(self.node, BasePath):
            return self.node.resolve(obj)
        elif isinstance(self.node, BaseFactory):
            node = self.node.build(obj, self.name)
            if not isinstance(node, BaseNode):
                raise ValueError(f'factory {self.name} does not resolve to a node object')
            return node 
        return self.node         

    def is_readable(self):
        return self.mode == NodeMode.R or self.mode == NodeMode.RW 

    def is_writable(self):
        return self.mode == NodeMode.W or self.mode == NodeMode.RW 


    @classmethod
    def from_field(cls, name, field, node_key=C.NODE):
        if node_key in field.field_info.extra:
            node = field.field_info.extra[node_key]
        else:
            if "." in name:
                node = ObjPath(name)
            else:
                node = AttrPath(name)
        
        if isinstance( node, (BasePath, str, tuple, list)):
            node = objpath(node)
        elif not isinstance(node, BaseNode):
            if not isinstance(node, BaseFactory):
                raise ValueError( f"Invalid node argument expecting a BaseNode, a Factory or string got {node}")
        
        node_var = field.type_
        mode = _node_var2mode(node_var) 
        return cls(node, name, mode=mode)
    
    @classmethod
    def from_member(cls, name, type_):
        mode=_node_var2mode(type_)
        return cls( AttrPath(name), name, mode=mode)
  
@dataclass
class SingleNodeField(NodeField):
    node: Union[ObjPath, BaseNode, BaseFactory] = ObjPath(".")
    name: str = "value"
    mode: NodeMode = NodeMode.RW
    def resolve(self, obj):
        if not isinstance(obj, BaseNode):
            return ValueError("Expecting a node object")
        return obj

    @classmethod
    def from_field(cls, name, field):
        return cls( )
    @classmethod
    def from_member(cls, name, type_):
        return cls()


@dataclass
class StaticField:
    path: BasePath
    name: str
    value: Optional[Any] = None
    def resolve(self, obj):
        return self.path.resolve(obj)

    @classmethod
    def from_field(cls, name, field):
        if C.PATH in field.field_info.extra:
            path = objpath(field.field_info.extra[C.PATH] )
        elif C.ATTR in field.field_info.extra:
            warn( f"{C.ATTR} var in field is deprecated, use {C.PATH!r}" , DeprecationWarning)
            path = ObjPath(field.field_info.extra[C.ATTR] )
        elif C.ITEM in field.field_info.extra:
            warn( f"{C.ITEM} var in field is deprecated, use {C.PATH!r}" , DeprecationWarning)
            item = field.field_info.extra[C.ITEM] 
            path = ObjPath(f"['{item}']")
        else:
            if "." in name:
                path = ObjPath(name)
            else:
                path = AttrPath(name)
        return cls(path, name)
    
    @classmethod
    def from_member(cls, name, type_):
        return cls(AttrPath(name), name) 

@dataclass
class ObjField:
    path: BasePath
    name: str
    
    def resolve(self, obj):
        child = self.path.resolve(obj)
        if not hasattr( child, "__dict__"):
            raise ValueError(f"{self.name!r} member is not an object")
        return child 

    @classmethod
    def from_field(cls, name, field):
        if C.PATH in field.field_info.extra:
            path = objpath(field.field_info.extra[C.PATH] )
        elif C.ATTR in field.field_info.extra:
            warn( f"{C.ATTR} var in field is deprecated, use {C.PATH!r}" , DeprecationWarning)
            path = ObjPath(field.field_info.extra[C.ATTR] )
        elif C.ITEM in field.field_info.extra:
            warn( f"{C.ITEM} var in field is deprecated, use {C.PATH!r}" , DeprecationWarning)
            item = field.field_info.extra[C.ITEM] 
            path = ObjPath(f"['{item}']")
        else:
            if "." in name:
                path = ObjPath(name)
            else:
                path = AttrPath(name)

        return cls(path, name)   
    
    @classmethod
    def from_member(cls, name, type_):
        return cls(AttrPath(name), name) 
    

@dataclass
class DataFields:
    nodes: List[NodeField] = field( default_factory=list)
    objects: List[ObjField] = field(default_factory=list)
    statics: List[StaticField] = field(default_factory=list)

class BaseExtractor:
    def extract(self, model)-> DataFields:
        raise NotImplementedError()

@dataclass
class PydanticModelExtractor(BaseExtractor):
    node_key: str = C.NODE
    def extract(self, model) -> DataFields:
        output = DataFields()
        fields = get_fields(model)
        
        for name, field in fields.items():
            if not isinstance(field.type_, type):
                continue 
            if issubclass(field.type_, StaticVar):
                output.statics.append( StaticField.from_field(name, field)  )
            elif issubclass(field.type_, NodeVar):
                output.nodes.append( NodeField.from_field( name, field, self.node_key) )
            else:
                output.objects.append( ObjField.from_field( name, field))
        return output

class NormalClassExtractor(BaseExtractor):
    def extract(self, cls: Type) -> DataFields:
        output = DataFields()
        if not hasattr( cls, "__dict__"):
            pass 
            
        annotations = get_annotations(cls)
        for name in dir (cls):
            if name.startswith("__"): continue 
            try:
                origin = _get_node_var_annotation( annotations, name)
            except (AttributeError, KeyError, ValueError):
                pass 
            else:
                if issubclass(origin, NodeVar):
                    output.nodes.append( NodeField.from_member(name, origin) )
                    continue
                elif issubclass(origin, StaticVar):
                    output.statics.append( StaticField.from_member(name, origin))
                    continue 
            
            obj = getattr(cls, name)
            if isinstance( obj, type): continue 
            if hasattr(obj, "__dict__"):
                output.objects.append( ObjField.from_member( name, annotations.get(name, None)))
        return output


class SingleNodeModelExtractor(BaseExtractor):
    def extract(self, model):
        output = DataFields()
        fields = get_fields(model)
        
        if not "value" in fields:
            raise ValueError("expecting a .value attribute for single node link")
        
        for name, field in fields.items():
            if not isinstance(field.type_, type):
                continue 
            if issubclass(field.type_, StaticVar):
                output.statics.append( StaticField.from_field(name, field)  )
            elif issubclass(field.type_, NodeVar):
                if name != "value":
                    raise ValueError("NodeVar is not allowed for single node link")
        
        output.nodes.append( SingleNodeField.from_field( "value", fields["value"] ) )
        return output

class SingleNodeNormalClassExtractor(BaseExtractor):
    def extract(self, cls):
        output = DataFields()
        annotations = get_annotations(cls)

        if not "value" in dir(cls):
            raise ValueError("expecting a .value attribute for single node link")
        for name in dir(cls):
            if name.startswith("__"): 
                continue 
            try:
                origin = _get_node_var_annotation( annotations, name)
            except (AttributeError, KeyError, ValueError):
                pass 
            else:
                if issubclass(origin, StaticVar):
                    output.statics.append( StaticField.from_member(name, origin))
                    continue 
                if issubclass(origin, NodeVar):
                    if name != "value":
                        raise ValueError("NodeVar is not allowed for single node link")
        output.nodes.append( SingleNodeField.from_member( "value", annotations.get(name, None) ))
        return output  

        

@dataclass
class NodeDataLinks:
    nodes_info: Dict[BaseNode,NodeField] = field(default_factory=dict)
    readable_nodes: Dict[BaseNode, List[Tuple[str,Any]]] = field(default_factory=dict)
    writable_nodes: Dict[BaseNode, List[Tuple[str,Any]]] = field(default_factory=dict)


@dataclass
class NodeResolver:
    extractor:  BaseExtractor
    def resolve(self, fields: DataFields, obj:Any, data:Any, output=None):
        if output is None: 
            output = NodeDataLinks()

        for static in fields.statics:
            setattr( data, static.name , static.resolve(obj) )

        for node_field in fields.nodes:
            node = node_field.resolve(obj)
            pairs =  (node_field.name, data)

            try:
                target = getattr(data,  node_field.name)
            except AttributeError:
                pass
            else:
                if not isinstance( target, Enum):
                    try:
                        target.value 
                    except AttributeError:
                        pass
                    else:
                        pairs = ("value",  target)

            if node_field.is_readable():
                output.readable_nodes.setdefault( node, []).append(  pairs) 
            if node_field.is_writable():
                output.writable_nodes.setdefault( node, []).append(  pairs) 
            output.nodes_info[node] = node_field

        for obj_field in fields.objects:
            try:
                sub_obj = obj_field.resolve(obj)
            except (KeyError, AttributeError) as e:
                pass
            else:
                if hasattr(sub_obj, "__dict__"):
                    sub_data =  getattr(data, obj_field.name)
                    sub_fields = self.extractor.extract(type(sub_data)) 
                    self.resolve( sub_fields, sub_obj, sub_data, output) 
        return output


def _get_node_var_annotation(annotations, name):
    
    annotation = annotations[name]
    try:
        return annotation.__origin__ # warning can be broken on other python version !!! ?? 
    except AttributeError:
        if issubclass(annotation, (NodeVar, StaticVar)): 
            return annotation
        raise ValueError()    
    
def collect_nodes( input, model, output: Optional[NodeDataLinks] = None, node_key=C.NODE) -> Union[None, NodeDataLinks]:
    """ return a :class:`NodeDataLinks` object from the match of an object and a data model instance 

    Function mainly used by :class:`DataLink` to build the depences between nodes and data
    """
    return_output = False
    if output is None:
        output = NodeDataLinks() 
        return_output = True 
    if isinstance(input, BaseNode):
        if isinstance( model, BaseModel):
            extractor = SingleNodeModelExtractor()
        else:
            extractor = SingleNodeNormalClassExtractor()
    else:
        if isinstance( model, BaseModel):
            extractor = PydanticModelExtractor(node_key=node_key)
        else:
            extractor = NormalClassExtractor()
    resolver = NodeResolver(extractor)

    fields = extractor.extract( type(model))
    resolver.resolve(fields, input, model, output)
    
    if return_output:
        return output


class DataLink(BaseDataLink):
    """ Link an object containing nodes, to a :class:`pydantic.BaseModel` 
    
    
    

    Args:
        input (Any):  Any object with attributes, expecting that the input contains some 
                      :class:`BaseNode` attributes in its hierarchy and eventualy some other 
                      pydevmgr object to be linked with the data 
                         
        model (:class:`pydantic.BaseModel`, Any): a data model or a normal class (e.i. dataclass). 
            Is expecting that the data structure 
            contains some :class:`NodeVar` type hint signature and eventually some sub models.
            DataLink accept also basic classes with annotations when complicate links are not needed  
        *other_models : if you have more model to linkd with the input object   

    Example of valid data (assuming pos_actual and pos_error are nodes of ``device.stat``):

    Before 

    ::

        from pydevmgr_core import NodeVar 
         
        class Data:
            pos_actual: NodeVal = 0.0 
            pos_error: NodeVar = 0.0
        
    
    :: 
        
        from pydevmgr_core import NodeVar 
        from dataclasses import dataclass 
        
        @dataclass
        class Data:
            pos_actual: NodeVal = 0.0 
            pos_error: NodeVar = 0.0
       
    :: 
        
        from pydevmgr_core import NodeVar 
        from pydantic import BaseModel, Field
        from pydantic_core.nodes import UtcTime  
        
        class Data(BaseModel):
            pos_actual: NodeVal = 0.0 
            pos_error: NodeVar = 0.0
            time: NodeVar = Field( '1950-01-01T00:00:00.00000', node=UtcTime() )
        
        data = Data()
        dl = DataLink( my_device.stat , data)
        dl.download()

    Above the node parameter in Field is setting the node (no match to the object)
    node argument can also be a string path to the node :

    ::
        
        from pydevmgr_core import NodeVar 
        from pydantic import BaseModel, Field
        from pydantic_core.nodes import UtcTime  
        
        class Data(BaseModel):
            pos_actual: NodeVal = Field(0.0, node="stat.pos_actual")
            pos_error: NodeVar  = Field(0.0, node="stat.pos_error") 
            time: NodeVar = Field( '1950-01-01T00:00:00.00000', node=UtcTime() )
        
        data = Data()
        dl = DataLink( my_device  , data)
        dl.download()
       
    Data link try also to match input object structure and data strucure

    ::

          
        from pydevmgr_core import NodeVar 
        from pydantic import BaseModel, Field
        from pydantic_core.nodes import UtcTime  
        
        class StatData:
            pos_actual: NodeVal = 0.0 
            pos_error: NodeVar = 0.0
        
        class Data:
            stat = StatData()
            time: NodeVar = Field( '1950-01-01T00:00:00.00000', node=UtcTime() )
        
        data = Data()
        dl = DataLink( my_device , data)
        dl.download()

            
    """
    def __init__(self, 
          input : Any, 
          model : BaseModel,
          *other_models, 
          node_key: str = C.NODE
        ) -> None:
        
        self._rnode_fields = {}
        self._wnode_fields = {}
        node_fields = collect_nodes(input, model, node_key=node_key)
        for other in other_models:
            collect_nodes( input, other, node_fields, node_key=node_key)


        self._rnode_fields = node_fields.readable_nodes
        self._wnode_fields = node_fields.writable_nodes

        self._input = input 
        self._model = model

    @property
    def model(self)-> BaseModel:
        return self._model    
    
    @property
    def input(self)-> Any:
        return self._input
    
    @property
    def rnodes(self)-> Iterable:
        return self._rnode_fields
    
    @property
    def wnodes(self)-> Iterable:
        return self._wnode_fields
         

    def download_from_nodes(self, nodevals: Dict[BaseNode,Any]) -> None:
        """ Update the data from a dictionary of node/value pairs
        
        If a node in the dictionary is currently not part of the data model it is ignored silently 
        """
        for node, val in nodevals.items():
            try:
                lst = self._rnode_fields[node]
            except KeyError:
                pass
            else:
                for attr, obj in lst:
                    setattr(obj, attr, val)
                    
    def _download_from(self, data: dict) -> None:
        for node, lst in self._rnode_fields.items():
            for attr, obj in lst:
                setattr(obj, attr, data[node])
                
    def download(self) -> None:
        """ download Nodes from servers and update the data """
        data = {}
        download( self._rnode_fields, data )
        self._download_from(data)
    
    def reset(self):
        """ All linked nodes with a reset method will be reseted """   
        reset(self._rnode_fields)
        reset(self._wnode_fields)         
                
    def _upload_to(self, todata: dict) -> None:
        for node, lst in self._wnode_fields.items():    
            for attr, obj in lst:
                val = getattr(obj, attr)
                if isinstance(val, BaseNode):
                    continue
                # the last in the list will be set
                # which may not in a hierarchical order 
                # any way several same w-node should be avoided
                todata[node] = val  
                        
    def upload(self) -> None:
        """ upload data value (the one linked to a node) to the server """
        todata = {}
        self._upload_to(todata)
        upload(todata) 

def _model_subset(
       class_name: str, 
       Model: Type[BaseModel], 
       fields: List[str], 
       BaseClasses: tuple =(BaseModel,)
    ) -> Type[BaseModel]:
    """ From a pydantic model class create a new model class with a subset of fields 
    
    Args:
        class_name (str): name of the create class model 
        Model (BaseModel): Model root 
        fields (List[str]): list of Model field names 
        BaseClasses (optional, tuple): base classes of the new class default is (BaseModel,)
    """
    annotations = {}
    new_fields = {}
    for field_name in fields:
        field = Model.__fields__[field_name]
        fi = field.field_info
        kwargs = dict(            
            description = fi.description, 
            ge=fi.ge, 
            gt=fi.gt, 
            le=fi.le, 
            lt=fi.lt,
            max_items=fi.max_items, 
            max_length=fi.max_length, 
            min_items=fi.min_items, 
            min_length=fi.min_length, 
            multiple_of=fi.multiple_of, 
            title=fi.title,         
        )
        kwargs.update(fi.extra)
                
        new_field = Field(fi.default, **kwargs)
        annotations[field.name] = field.type_ 
        new_fields[field.name] = new_field
        
    new_class = type(class_name, BaseClasses, new_fields)  
    new_class.__annotations__ = annotations
    return new_class



