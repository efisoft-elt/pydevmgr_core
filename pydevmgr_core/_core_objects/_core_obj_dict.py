from math import isinf
from pydevmgr_core._core_objects._class_recorder import get_class, KINDS
from pydevmgr_core._core_objects._core_base import _BaseObject, CONFIG_MODE, CONFIG_MODE_DEFAULT, _BaseObjDict, _BaseObjDictProperty
from pydevmgr_core._core_objects._core_pydantic import _default_walk_set

from typing import Any, Type, Tuple, Optional
#from ._class_recorder import get_class, KINDS
#from ._core_base import _BaseObject



from pydantic import BaseModel, validator
import weakref


class ObjDictConfig(BaseModel):
    kinds: set  = set()
    types: set  = set()
    exclude_kinds: set = set()
    exclude_types: set = set()
    default_kind: Optional[KINDS] = None
    default_type: Optional[str] = None

class ObjDictProperty(_BaseObjDictProperty):

    def __init__(self, name, cls=None, config=None, config_path=None, config_mode=CONFIG_MODE_DEFAULT):
        self._name = name
        self._cls = ObjDict if cls is None else cls
        if config is None:
            config = self._cls.Config()
        self._config = config 
        self._config_path = config_path
        self._config_mode = config_mode
    
    def get_config(self, parent):
        """ return configuration from parent object """
        # this has to be implemented for each kinds
        if self._config_path:
            config = getattr( parent.config, self._config_path )
        elif self._name:

            try:
                config = getattr(parent.config, self._name+"_rules")
            except AttributeError:
                config = self._config
            
             
    
        if config is not self._config:
            if self._config_mode == CONFIG_MODE.DEFAULT:
                _default_walk_set(self._config, config)
            else:
                for k,v in self._config.dict( exclude_unset=True ).items():
                    # TODO: Add warning for config overwrite 
                    setattr(config, k, v)
        return config   

    def __get__(self, parent, pcls=None):
        if parent is None: 
            return self

        try:
            return parent.__dict__[self._name]
        except KeyError:
            
            cfg_dict = getattr(parent.config, self._name, {})
                            
            output = self._cls( cfg_dict, __parent__= parent, __config__= self.get_config(parent)  )
            
            # Cash the dictionary in parent 
            parent.__dict__[self._name] = output 
            return output
    
    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name 


class ObjDict(_BaseObjDict):
    Config = ObjDictConfig

    def __init__(self, __d__ = {}, __parent__= None, __config__= None, **kwargs):
        
        if __config__ is None:
            config = self.Config()
        elif isinstance(__config__, dict):
            config = self.Config.parse_obj(__config__)
        else:
            config = __config__

        d = dict(__d__, **kwargs)
        super().__init__( {name:self.validate_child(name, child, config, __parent__) for name, child in d.items() }) 
        

        if __parent__:
            self._parent_ref = weakref.ref(__parent__) 
        else:
            self._parent_ref = lambda : None
        
        self._config = config
    def __setitem__(self, key, value):
        value = self.validate_child(key, value, self._config, self._parent_ref())
        super().__setitem__(key, value)
       
    def update(self, __d__={}, **kwargs):
        d = {name:self.validate_child(name, child, self._config, self._parent_ref()) for name, child in dict(__d__, **kwargs).items()}
        super().update( d )
    

    @classmethod
    def validate_kind(cls, name, kind, config):
        if kind is None:
            if config.default_kind:
                return config.default_kind
            else:
                raise ValueError(f"children {name!r} no default kind")
            
        if config.kinds:
            if kind is None:
                return config.kinds[0]
            if (kind not in config.kinds) or (kind in config.exclude_kinds):
                raise ValueError(f"children {name!r}  does not have the right kind")
        elif kind in config.exclude_kinds: 
            raise ValueError(f"children {name!r}  does not have the right kind")
        return kind
    
    @classmethod
    def validate_type(cls, name, type_, config):
        if type_ is None:
            if config.default_type:
                return config.default_type
            else:
                raise ValueError(f"children {name!r} no default kind")
           
        if config.types:    
            if (type_ not in config.types) or (type_ in config.exclude_types):
                raise ValueError(f"children {name!r}  does not have the right type")
        elif type_ in config.exclude_types: 
            raise ValueError(f"children {name!r}  does not have the right type")
        return type_
     
    @classmethod
    def validate_config(cls, name, conf: BaseModel, config: BaseModel)-> Tuple[Type,BaseModel]:
        cls.validate_kind(name, getattr(conf, 'kind', None), config )
        cls.validate_type(name, getattr(conf, 'type', None), config )
        ObjClass = get_class(conf.kind, conf.type)
        return ObjClass, conf     
    
    @classmethod
    def validate_dict(cls, name, d: dict, config: BaseModel)-> Tuple[Type,BaseModel]:
        kind  = cls.validate_kind( name, d.get("kind", None), config )
        type_ = cls.validate_type( name, d.get("type", None), config )
        ObjClass = get_class(kind, type_)
        return ObjClass, ObjClass.Config.parse_obj(d)
 
    @classmethod
    def validate_object(cls, name, obj: Any, config):
        if not isinstance( obj, _BaseObject ):
            raise ValueError(f"child {name} of of type {type(obj)} is not allowed")
        cls.validate_kind( name, obj.config.kind, config )
        cls.validate_type( name, obj.config.type, config )

        return obj
    
  
    @classmethod
    def validate_child(cls, name, child, config, parent=None):
        if isinstance( child, _BaseObject):
            return cls.validate_object(name, child, config) 
        
        if isinstance(child, BaseModel):
            ObjClass, config = cls.validate_config( name, child, config )
        
        elif isinstance( child, dict ):
            ObjClass, config = cls.validate_dict( name, child, config )

        else:
            raise ValueError(f"Unexpected child type: {type(child)}")
        if parent:
            obj = ObjClass.new(parent, name, config=config)
        else:
            obj = ObjClass(key=name, config=config)
        return obj
    
    @classmethod
    def new(cls, parent, name=None, **kwargs):
        
        config = cls.Config(**kwargs)
         
        if name is None:
            cfg_dict = {}
        else:
            cfg_dict = getattr(parent.config, name)
        return cls( cfg_dict, __parent__= parent, __config__= config )


    @classmethod
    def prop(cls, name=None, **kwargs):
        config = cls.Config(**kwargs)
        return ObjDictProperty(name, cls, config=config)



if __name__ == "__main__":
    from pydevmgr_core import BaseDevice, BaseManager, record_class
    from pydevmgr_core._core_objects._core_pydantic import GenDevice
    from typing import Dict 

    @record_class
    class D(BaseDevice):
        class Config(BaseDevice.Config):
            type = "D"
            num: int = 0 
    
    class M(BaseManager):
        class Config(BaseManager.Config):
            devices: Dict[str, GenDevice] = { 'dev1': D.Config(num=1)}

        devices = ObjDict.prop('devices') 

    assert M().devices['dev1'].config.num == 1
