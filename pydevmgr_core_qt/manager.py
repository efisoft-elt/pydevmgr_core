from PyQt5.QtWidgets import QLayout, QBoxLayout, QGridLayout, QWidget
from PyQt5 import QtCore
from .base import get_widget_factory, BaseUiLinker, WidgetFactory
from typing import List, Tuple, Optional
from pydevmgr_core import BaseDevice

def insert_widget(
     device: BaseDevice, 
     layout: QLayout, 
     widget_kind: str, *,
     default_factory: Optional[WidgetFactory] = None,
    
     column: int = 0,
     row: int = 0,
     columnSpan: int = 1,
     rowSpan: int = 1,
     
     stretch: int = 0,
     alignment: int = 0        
    ) -> BaseUiLinker:
    """ Insert one device widget inside a QT Layout object 
    
    Args:
        device (BaseDevice): list of devices 
        layout: (QLayout)
        widget_kind (str):  e.g. "line", "ctrl", "cfg" 
        
    
    Returns:
       linker (BaseUiLinker): A device linker object (not yet connected to device)
       
    """
    factory = get_widget_factory(widget_kind, device.config.type, default=default_factory)       
    linker = factory.build()
    
    widget = linker.widget 
    if isinstance(layout, QBoxLayout): 
        layout.addWidget(widget, stretch, QtCore.Qt.AlignmentFlag(alignment))
    elif isinstance(layout, QGridLayout):
        layout.addWidget(widget, row, column, rowSpan, columnSpan)
    else:
        layout.addWidget(widget)  
    return linker 

def insert_widgets(
      devices: List[BaseDevice], 
      layout: QLayout, 
      widget_kind: str, *, 
      direction: int = 0, # 0 for row 1 for column
      column: int = 0,
      row: int = 0,
      **kwargs
    ) -> List[Tuple[BaseDevice,BaseUiLinker]]:
    """ Insert devices widgets inside a QT Layout object 
    
    Args:
        device (list): list of devices 
        layout: (QLayout)
        widget_kind (str):  e.g. "line", "ctrl", "cfg" 
        
    
    Returns:
       device_linker (list): A list of (device, linker) tuple
       
    """
    
    if direction:
        return [(device,insert_widget(device, layout, widget_kind, column=column+i, row=row, **kwargs)) for i,device in enumerate(devices)]
    else:
        return [(device,insert_widget(device, layout, widget_kind, row=row+i, column=column, **kwargs)) for i,device in enumerate(devices)]
        
        

