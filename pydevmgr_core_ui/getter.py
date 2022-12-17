from dataclasses import dataclass
from typing import Any, Optional, Type

from pydantic.main import BaseModel


class BaseGetter:
    def get(self, container: Any):
        raise NotImplementedError

    def get_func(self, container):
        def get():
            return self.get(container)
        return get


@dataclass
class GetLink:
    getter: BaseGetter
    container: Any
    def get(self):
        return self.getter(self.container)


getter_loockup = {}
def record_getter( widget_type: str, python_type: Type):
    key_loockup = ( widget_type, python_type)
    def record(cls):
        getter_loockup[key_loockup] = cls
        return cls
    return record 

def get_getter_class( widget_type: str, python_type: Type):
    try:
        return getter_loockup[ ( widget_type, python_type) ] 
    except KeyError:
        raise ValueError( f"cannot found getter for {widget_type} for a {python_type}")
    


class WidgetDataGetter:
    Data: BaseModel
    mapping: dict 
    groups: dict 

    default_getter = None 
    def __init__(self, Data: Type[BaseModel] ):
        self.Data = Data
        self.mapping = {}
        self.groups = {}

        for key, field in Data.__fields__.items():
            if issubclass( field.type_, BaseModel):
                self.groups[key] = WidgetDataGetter(field.type_ )
            else:
                try:
                    widget_attr = field.field_info.extra['widget']
                except KeyError:
                    continue

                getter = field.field_info.extra.get('getter', self.default_getter)
                if getter is None:
                    raise ValueError(f"No default getter, need a getter for attribute {key}")

                self.mapping[key] = (getter, widget_attr)
   
    def get(self, widget, data: Optional[BaseModel]=None):
        """ Fill up the data structure from widget entries """
        if data is None: data = self.Data()
        for key, (getter, wattr) in self.mapping.items():
            setattr( data, key, getter.get( getattr(widget, wattr)))
        for key, group in self.groups.items():
            setattr( data,  key, group.get( widget ))

