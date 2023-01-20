from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple, Type, Union
from pydantic.fields import Field
from pydantic.main import BaseModel, create_model

from systemy.system import BaseFactory
from pydevmgr_core.base.base import BaseData, BaseObject, find_factories
from pydevmgr_core.base.model_var import NodeVar
from pydevmgr_core.base.node import BaseNode

from pydevmgr_core.base.vtype import VType, find_vtype, _vtype_default, _vtype_type

def get_fields(model: BaseModel):
    return model.__fields__


@dataclass
class ModelNode:
    name: str
    key: str
    vtype: VType
    factory: BaseFactory
    Data: Optional[Type[BaseModel]] = None 

@dataclass
class ModelGroup:
    name: str
    key: str
    nodes: List[ModelNode] = field(default_factory=list)
    groups: List = field(default_factory=list)
    Data: Optional[Type[BaseModel]] = None 


    
def _feed_factory_memberf_to_model(model, factory):
    for name in get_fields(model):    
        try:
            value = getattr(factory, name) 
        except AttributeError:
            pass 
        else:
            setattr(model,name, value)

  
    
def _total_nuber_of_nodes(group: ModelGroup):
    return len(group.nodes) + sum( _total_nuber_of_nodes(g) for g in group.groups) 

def _get_path_model(root: str, definition: Union[ModelGroup, ModelNode]) -> str:
    if not root:
        return definition.name 
    if definition.startswith(root+"."):
        return definition.key[len(root)+1:] 
    return definition.name 



@dataclass
class ObjectToDataModelExtractor:
       
    def extract(self, 
            name:str, 
            objects: Iterable, 
            depth:int  = -1
        )-> ModelGroup:
        group = ModelGroup(name=name, key=name)
        
        for obj in objects:
            if isinstance(obj, tuple):
                attr, factory = obj 
                ClassesToDataModelExtractor().extract_item(group, attr, factory, depth) 
            elif isinstance( obj, BaseNode):
                self.extract_node(group, obj) 
            elif depth:
                self.extract_subgroup(group, obj, depth) 
        return group
    
    def extract_node(self, group: ModelGroup, node: BaseNode)-> None:
        model_def =  ModelNode(
                        node.name, 
                        node.key, 
                        find_vtype(node), 
                        node.config, 
                        Data = node.Data        
                    )
        group.nodes.append(model_def)
    
    def extract_subgroup(self, group:ModelGroup, obj:BaseObject, depth: int)-> None:
        sub_group = self.extract(obj.name, obj.find(BaseObject), depth-1)
        sub_group.Data = getattr(obj, "Data", None)
        sub_group.key = obj.key
        group.groups.append(sub_group)



@dataclass
class ClassesToDataModelExtractor:
    
    def extract(self, 
          name: str, 
          cls: Type[BaseObject], 
          depth:int = -1
        )-> ModelGroup:
        
        if isinstance(cls, type):
            factories = find_factories(cls)
        elif isinstance(cls, dir):
            factories = cls.items 
        else:
            factories = cls 
        
        group = ModelGroup(name=name, key=name)
        
        for attr, factory in factories:
            self.extract_item( group, attr, factory, depth)    
        return group
    

    def extract_item(self, group, attr, factory, depth)->None:
        try:
            System  = factory.get_system_class()
        except ValueError:
            return 
        
        if issubclass( System, BaseNode):
            self.extract_node(group, attr, factory)
        elif depth:
            self.extract_subgroup( group, attr, factory, depth) 


    def extract_node(self, group, attr, factory)-> None:
        System  = factory.get_system_class()
        model_def = ModelNode(
                name=attr,
                key=attr, 
                vtype=find_vtype(factory), 
                factory = factory, 
                Data = System.Data
            ) 
        group.nodes.append(model_def)
    
    def extract_subgroup(self, group, attr, factory, depth):
        System = factory.get_system_class() 
        sub_group =  self.extract(attr, System, depth-1)
        sub_group.Data = getattr( System, "Data", None)
        group.groups.append( sub_group)




@dataclass
class DataModelCreator:
    root: str = ""
    with_vtype_only: bool =False 
    use_data_if_defined: bool =True 
    NodeModel: Optional[Type[BaseModel]] = None 

    def create(self, group, base_class: Optional[Type[BaseModel]] = None):
        if self.use_data_if_defined and group.Data:
            if isinstance(group.Data, type):
                if not (group.Data is BaseData or group.Data is BaseModel) :
                    return group.Data 
        members = {}
        for node_def in group.nodes:
            
            if self.NodeModel:
                vtype, default = self.NodeModel, self.NodeModel()
                _feed_factory_memberf_to_model( default, node_def.factory )    
                default.value = _vtype_default(node_def.vtype)

            else:
                vtype, default = _vtype_type(node_def.vtype), _vtype_default(node_def.vtype)

            if vtype is None:
                if self.with_vtype_only:
                    continue 
                field = (NodeVar, Field(default, node=_get_path_model(self.root, node_def) ))
            else:
                field = (NodeVar[vtype], Field(default,node=_get_path_model(self.root, node_def)))
            members[node_def.name] = field 

        for sub_group in group.groups:
            if not _total_nuber_of_nodes(sub_group): continue
            SubModel = self.create(sub_group)
            members[sub_group.name.capitalize()] = SubModel 
            members[sub_group.name.lower()] = (SubModel, Field(SubModel(), path=_get_path_model(self.root, sub_group)))
        


        class Config:
            arbitrary_types_allowed = True 
        return create_model( group.name.capitalize(), __base__=base_class, Config=Config, **members) 


@dataclass
class CodeModelCreator:
    root: str = ""
    with_vtype_only: bool =False
    NodeModel: Optional[Type[BaseModel]] = None 

    def create(self, 
          group: ModelGroup,
          base_class: Optional[Type[BaseModel]] = BaseModel,
          indent=0, 
        )->str:

        text  = []
        spaces = "    "
        text.append( spaces*indent + f"class {group.name.capitalize()}({base_class.__name__}):")
        indent += 1

        for node_def in group.nodes:
            if self.NodeModel:
                vtype, default = self.NodeModel, self.NodeModel()
                _feed_factory_memberf_to_model( default, node_def.factory )    
                default.value = _vtype_default(node_def.vtype)

            else:
                vtype, default = _vtype_type(node_def.vtype), _vtype_default(node_def.vtype)



            node_path = _get_path_model(self.root, node_def)
            if node_path == node_def.name:
                if vtype:
                    l = f"{node_def.name}: NodeVar[{vtype.__name__}] = {default!r}"
                else:
                    l = f"{node_def.name}: NodeVar = {default!r}"
            else:
                if vtype:
                    l = f"{node_def.name}: NodeVar[{vtype.__name__}] = Field( {default!r}, node={node_path!r})"
                else:
                    l = f"{node_def.name}: NodeVar = Field( {default!r}, node={node_path!r})"
            text.append( spaces*indent+l )
        
        for sub_group in group.groups:
            if not _total_nuber_of_nodes(sub_group): continue
            sub_text = self.create(
                    sub_group,
                    indent= indent 
                )
            text.append(sub_text)
            group_path = _get_path_model(self.root, node_def)
            if group_path == node_def.name:

                text.append( spaces*indent + f"{sub_group.name.lower()}:  {sub_group.name.capitalize()}  = {sub_group.name.capitalize()}()")
            else:
                text.append( spaces*indent + f"{sub_group.name.lower()}:  {sub_group.name.capitalize()}  = Field({sub_group.name.capitalize()}(), path={group_path!r})")
        return "\n".join(text) 




def create_data_model(
        name: str, 
        objects: Union[Iterable[BaseObject],Iterable[Tuple[str, BaseFactory]], Type[BaseObject]],
        root: Union[BaseObject, str] = "", 
        base_class: Optional[Type] = None, 
        depth:int =-1, 
        with_vtype_only=False,
        use_data_if_defined=True, 
        NodeModel: Optional[Type[BaseModel]] = None, 
        create_code=False
    )-> BaseModel:
    """ Create a new data class for the object according to a list of objects 

    the following rule is applied to childs:
        - if a BaseNode it is added to the model as NodeVar with type Any and a default value None
        - in case of an other object (e.g. Device, Manager, etc ...):
            - if a Data class is defined (and not a BaseModel or a BaseData) it is instanciated in the model 
            - otherwise create_data_model will build a new data model for the child object 

    By default create_data_model is done recursively for anyking of object. However depth can be adjusted 
    with the keyword depth (default depth=-1). ``depth=0`` will create the date model only for nodes find inside
    the list of objects. 
    
    
    .. warning::

        Important note the data attribute is the object name. If two object have the same name this will create only 
        one data field. 
        
    """   
    if isinstance( objects, type):
        group_extractor = ClassesToDataModelExtractor()
    elif hasattr(objects, "__iter__"):
        group_extractor = ObjectToDataModelExtractor()
    else:
        raise ValueError("Expecting a Type[BaseObject] or a list of instancied objects") 
     
    if isinstance( root, BaseObject):
        root = root.key  
    
    group = group_extractor.extract(name, objects, depth)
    if create_code:
        creator = CodeModelCreator( root=root, with_vtype_only=with_vtype_only) 
    else:
        creator = DataModelCreator( 
                    root=root, with_vtype_only=with_vtype_only, 
                    use_data_if_defined=use_data_if_defined, 
                    NodeModel=NodeModel 
                )
    return creator.create(group, base_class)



def set_data_model(__cls__=None, name="Data", exclude: Optional[set] =None, include: Optional[set]=None):
    """ Create a data model for a given class 

    Store the model inside the .Data attribute 
    Return the class so it can be used at decroator 
    """
    def data_model_setter(cls):
        Data = create_data_model( name, find_factories(cls, include=include, exclude=exclude)) 
        setattr( cls, name, Data)
        return cls 

    if __cls__:
        return data_model_setter(__cls__)
    else:
        return data_model_setter 
  


# ##################################################################
#
#        Model Info Extractor 
#
# ##################################################################

@dataclass
class DataModelInfoExtractor:
    InfoStructure: BaseModel 
    include: Optional[Iterable] = None 
    exclude: Iterable = field(default_factory=set)
    include_type : Optional[Union[Type,Tuple[Type]]] = None
    exclude_type: Optional[Union[Type,Tuple[Type]]] = None

    def __post_init__(self):
        self.field_extractor = ModelInfoFieldExtractor( self.InfoStructure)


    def extract(self, Data: Type[BaseModel], name=None, base=None):
                
        infos = {}
        fields = get_fields(Data)
        if self.include is not None:
            def iterator():
                for name in set(self.include):
                    yield name, fields[name] 
        else:
            iterator = fields.items
        
        for name, field in iterator():
            if name in self.exclude: 
                continue
            if self.exclude_type:
                if issubclass( field.type_, self.exclude_type):
                    continue
            if issubclass(field.type_, BaseModel):
                infos[name] = self.extract( field.type_)()
            else:
                if self.include_type:
                    if not issubclass( field.type_, self.include_type): continue 
                        
                infos[name] = (self.InfoStructure, self.field_extractor.extract(field))
        if name is None:
            name = "Info"+Data.__name__
        return create_model(name,__base__ = base, **infos)


@dataclass 
class ModelInfoFieldExtractor:
    InfoStructure: BaseModel 
    def __post_init__(self):
        info_fields = get_fields(self.InfoStructure)
        
        def extract(field):
            extras = field.field_info.extra
            values = {}
            for name in info_fields:
                try:
                    val = getattr(field.field_info, name)
                except AttributeError:
                    try:
                        val = extras[name]
                    except KeyError:
                        pass 
                    else:
                        values[name] = val 
                else:
                    if val is not None:
                        values[name] = val 
    
            return self.InfoStructure(**values) 

        self.extract = extract

def create_model_info(
        Data: Type[BaseModel],  
        InfoStructure: Type[BaseModel],
        include: Optional[Iterable] = None, 
        exclude: Iterable = None, 
        include_type: Union[Type,Tuple[Type]] = None, 
        exclude_type: Union[Type,Tuple[Type]] = None, 
        name: str =None, 
        base: Type = None
    ) -> Type[BaseModel]:
    """ create a pydantic model representing all information found in an other model class 

    Args:
        Data  (Type[BaseModel]): a Model with some value and some extra field information 
        InfoStructure (Type[BaseModel]): The Model representing information to be extracted 
        include (Optional, Set[str]): A set of member name to include 
        exclude (Optional, Set[Str]): A sett of member to exclude  
        include_type: (Optional, Type, Tuple[Type]): include only members with the given type(s)
        exclude_type: (Optional, Type, Tuple[Type]): exclude member with the given type(s) 
    """
    if exclude is None: exclude = set()
    
    return DataModelInfoExtractor(
            InfoStructure, include=include, exclude=exclude, 
            include_type=include_type, exclude_type=exclude_type
        ).extract(Data, name=name, base=base)

