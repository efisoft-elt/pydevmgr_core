from dataclasses import dataclass
from typing import Type

@dataclass
class BaseBuilder:
    def build(self, widget, obj):
        raise NotImplementedError("build")

builder_loockup = {}
def record_builder( widget_type: str, python_type: Type):
    key_loockup = ( widget_type, python_type)
    def record(cls):
        builder_loockup[key_loockup] = cls
        return cls
    return record 

def get_builder_class( widget_type: str, python_type: Type):
    try:
        return builder_loockup[ ( widget_type, python_type) ] 
    except KeyError:
        raise ValueError( f"cannot found builder for {widget_type} for a {python_type}")
    



