from PyQt5 import  uic
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QComboBox, QWidget
from .base import get_widget_types, BaseUiLinker, get_widget_factory, DEFAULT, LayoutLinker
from pydantic import BaseModel
from typing import Optional, List
from pydevmgr_core import BaseDevice
from .io import find_ui


class SwitchUi(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(find_ui('switch.ui'), self)
        
class SwitchLinker(BaseUiLinker):
    Widget = SwitchUi
    _linker = None
    layout_linker = None
    
    class Data(BaseModel):
        default_widget_type: str = ""
        curent_widget_type:  str = ""
        widget_type_list: Optional[List[str]] = None 
        
    def update(self, data):
        pass
    
    def connect(self, 
           downloader, obj, data = None, 
           link_failure: Optional[bool] = DEFAULT.link_failure , 
           link_update: Optional[bool] = DEFAULT.link_update         
        ):
        #if data is None:
        #    data = self.Data()
        self.layout_linker = LayoutLinker(self.widget.device_layout)
        self.layout_linker.connect(downloader)
        #self.setup_ui(obj, data)
        super().connect(downloader, obj, data, link_failure=link_failure, link_update=link_update)
            
    def setup_ui(self, device, data):
        if data.widget_type_list is None:
            data.widget_type_list =  get_widget_types(device.config.type)
        if not data.widget_type_list:
            raise ValueError(f"No Widget found for device of type {device.config.type}")
        if not data.default_widget_type:
            data.default_widget_type = data.widget_type_list[0]
                
        self.widget.style_switch.clear()    
        for wtype in data.widget_type_list:
            self.widget.style_switch.addItem(wtype)
        self.widget.style_switch.setCurrentIndex(0)
        
        
        def on_switch_changed(wt):
            # clear the layout
            self.layout_linker.clear()
            self.layout_linker.add_device(device, wt)
            data.curent_widget_type = wt
            
        
        self.actions.add(
            on_switch_changed, 
            [self.widget.style_switch.currentText], 
        ).connect_combo(self.widget.style_switch)
        
        # load with the first widget on the list or default 
        if data.default_widget_type and data.default_widget_type in data.widget_type_list:        
            on_switch_changed(data.default_widget_type)
        else:
            on_switch_changed(data.widget_type_list[0])
        
            
            
                