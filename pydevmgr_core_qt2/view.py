from PyQt5.QtWidgets import QLayout, QWidget
from pydantic import BaseModel 
from typing import Dict, Iterable, Union, List, Optional
import glob 

class ViewSetupConfig(BaseModel):
    """
     configuration of one view setup 

    Args:
        layout (str) : name of the layout in the ui used to publish widget (default is 'ly_devices')
        dev_type (iterable, str): Accepted device type names, e.g. ["Motor", "Drot"]
        alt_dev_type (str, None) : If not found look at a widget defined for a `alt_dev_type`
        exclude_device (str, iterable): exclude the device with the given names
        exclude_dev_type (str, iterable): exclude device with the given types
        widget_kind (str): string defining the widget kind (default, 'ctrl')
        alt_layout (iterable, str): Alternative layout name if `layout` is not found
        
        column, row, columnSpan, rowSpan, stretch, alignment : for layout placement. 
                The use depend of the nature of the layout (Grid, HBox, VBox) 
    """
    layout: str = "ly_devices" 
    device: Union[str, Iterable] = "*"
    dev_type: Union[str, Iterable]  = "*"
    alt_dev_type: Optional[List[str]] = None

    exclude_device: Union[str, Iterable] = ""
    exclude_dev_type: Union[str, Iterable]  = ""
    
    widget_kind: str = "ctrl"
    alt_layout: Union[str,Iterable] = [] 
    column: int = 0
    row: int = 0
    columnSpan: int = 1
    rowSpan: int = 1
    
    stretch: int = 0
    alignment: int = 0



class ViewConfig(BaseModel):
    setup: List[ViewSetupConfig] = ViewSetupConfig()
    size: Optional[List] = None
    ui_file: Optional[str] = None


class ViewsConfig(BaseModel):
    views: Dict[str, ViewConfig] = {} 



def _obj_to_match_func(obj):
    if not obj:
        return lambda name: False 
    if isinstance(obj, str):
        return lambda name: glob.fnmatch.fnmatch(name, obj)
    elif hasattr(obj, "__iter__"): 
        return  lambda name: name in obj

def filter_devices(devices, config: ViewSetupConfig = ViewSetupConfig() ):
        c = config
        output_devices = []
        match_device = _obj_to_match_func(c.device)
        match_type   = _obj_to_match_func(c.dev_type)
        
        exclude_match_device = _obj_to_match_func(c.exclude_device)
        exclude_match_type   = _obj_to_match_func(c.exclude_dev_type)
        for device in devices:        
            if exclude_match_device(device.name): continue
            if exclude_match_type(device.config.type): continue
            if match_device(device.name) and match_type(device.config.type):
                output_devices.append(device)  
        return output_devices

def find_layout(ui: QWidget, config:  ViewSetupConfig = ViewSetupConfig() ):
        """ find a layout from a parent ui according to config 
        
        Look for a layout named as .layout properties. If not found look inside 
        the .alt_layout list property. 
        """
        layout = ui.findChild(QLayout, config.layout)
        if layout is None:
            for ly_name in config.alt_layout:
                layout = ui.findChild(QLayout, ly_name)
                if layout: break
            else:
                raise ValueError(f"Cannot find layout with the name {layout!r} or any alternatives")
        return layout
   

