from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional, Tuple, Type, Union
from pydantic import BaseModel

from pydevmgr_core.base.object_path import AttrPath, BasePath, ObjPath 

class BaseSetter:
    def set(self, 
            container: Any, 
            value: Any, 
        ) -> None:
        raise NotImplementedError('set')

@dataclass
class SetLink:
    setter: BaseSetter
    container: Any
    def set(self, value):
        self.setter.set(self.container, value)


setter_loockup = {}
def record_setter(widget_type: str, python_type: Type):
    key_loockup = (widget_type, python_type)
    def record(cls):
        setter_loockup[key_loockup] = cls
        return cls
    return record 

def get_setter_class(widget_type: str, python_type: Type):
    try:
        return setter_loockup[ (widget_type, python_type) ] 
    except KeyError:
        raise ValueError( f"cannot found setter for {widget_type} for a {python_type}")
    

@dataclass
class UiInterface:
    widget: Optional[str] = None
    setter: Optional[Callable] = None
    getter: Optional[Callable] = None
    builder: Optional[Callable] = None 
    data: Optional[str] = None 


def _parse_path(obj, default):
    if not obj:
        if default is None:
            raise ValueError(f"expecting a string or a BasePath got a {type(obj)}")
        return  ObjPath(default)
    
    if isinstance(obj, str):
        if "." in obj or "[" in obj:
            return  ObjPath(obj)
        else:
            return AttrPath(obj)
        
    if isinstance(obj, BasePath):
        return obj
    raise ValueError(f"expecting a string or a BasePath got a {type(obj)}")


class WidgetDataSetter(BaseSetter):
    mapping: dict 
    groups: dict 
    default_setter = None

    _interface_key = "ui_interface"
    def __init__(self, Data: Type[BaseModel]):
        self.mapping = {}
        self.groups = {}
        

        for key, field in Data.__fields__.items():
            try:
                interface = field.field_info.extra[self._interface_key]
            except KeyError:
                if issubclass( field.type_, BaseModel):
                    self.groups[key] = self.__class__(field.type_)
                else:
                    continue
            else:
                widget_path = _parse_path( interface.widget, key)
                self.mapping[key] = (widget_path, interface.setter)# UiSetterInterface( path = path, setter= interface.setter)

    def set(self, widget, data: BaseModel):
        """ Update widget values from data """
        for  key, ( w_path, setter) in self.mapping.items(): 
            setter.set(w_path.resolve(widget), getattr(data, key))
        for key, group in self.groups.items():
            group.set( widget, getattr(data, key))

class UiInterfaces(BaseModel):
    pass

class DataToWidgetSetter(BaseSetter):
    mapping: list
    def __init__(self, Interfaces: Type[UiInterfaces]):
        self.mapping = []
        for key, field in Interfaces.__fields__.items():
            if issubclass(field.type_, UiInterface):
                pass
            interface = field.default
            if interface is None:
                interface = field.type_() 
                
            d_path = _parse_path(interface.data,   key)
            w_path = _parse_path(interface.widget, key)
            self.mapping.extend( (d_path, w_path, interface.setter) )
    
    def set(self, widget, data: BaseModel):
        for d_path, w_path, setter in self.mapping:
            setter.set( w_path.resolve(widget), d_path.resolve(data))
        
    
