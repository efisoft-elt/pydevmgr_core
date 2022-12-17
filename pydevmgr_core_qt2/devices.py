from dataclasses import dataclass, field
from PyQt5 import QtCore
from PyQt5.QtWidgets import QAction, QBoxLayout, QFrame, QGridLayout, QLayout, QMainWindow, QMenu, QScrollArea, QVBoxLayout, QWidget

from pydevmgr_core import BaseDevice, Downloader
from pydevmgr_core_qt.base_view import find_layout
from pydevmgr_core_qt.io import find_ui
from pydevmgr_core_qt2.base import get_ui_class
from pydevmgr_core_qt2.device import QtBaseDevice
from typing import Dict, List, Optional, Union, Iterable

from pydevmgr_core_qt2.view import ViewConfig, ViewsConfig, ViewSetupConfig, filter_devices
from pydevmgr_core_ui import Action,  BaseConnector, get_connector_class


@dataclass
class QtWidgetAppender:
    """ Class used to append an widget inside a layout """
    layout: QLayout 
    alt_layout: Union[str,Iterable] = field(default_factory=list) 
    
    stretch: int = 0
    alignment: int = 0 
    row: int = 0
    column: int = 0 
    rowSpan: int = 1 
    columnSpan: int = 1

    def append(self, widget: QWidget)-> None:
        layout = self.layout 
        
        if isinstance(layout, QBoxLayout): 
            layout.addWidget(widget, self.stretch, QtCore.Qt.AlignmentFlag(self.alignment))
        elif isinstance(layout, QGridLayout):
            layout.addWidget(widget, self.row, self.column, self.rowSpan, self.columnSpan)
        else:
            layout.addWidget(widget)        
    
 

def get_ui_child( 
        devices: List[BaseDevice], 
        container: QWidget, 
        setups: List[ViewSetupConfig]
    ):
    
    for setup in setups:
        matched_devices = filter_devices (devices, setup)
        appender = get_appender(container, setup)
        for device in matched_devices:
            ui_device = get_ui_class("qt", type(device), setup.widget_kind)(device) 
            ui_device.widget_appender = appender
            # yield UiChildDevice(ui_device, appender= appender)
            yield ui_device 
        

def get_appender(container: QWidget, setup_config: ViewSetupConfig):
    layout = find_layout(container, setup_config)      
    return QtWidgetAppender(layout=layout,  
            stretch = setup_config.stretch, 
            alignment = setup_config.alignment, 
            row = setup_config.row, 
            column = setup_config.column, 
            rowSpan = setup_config.rowSpan, 
            columnSpan =  setup_config.columnSpan 
        )

@dataclass
class ViewChildMaker:    
    class DefaultContainer(QFrame):
        def __init__(self, *arg, **kwargs):
            super().__init__(*arg, **kwargs)

            self.scroll = QScrollArea() 
            self.widget = QWidget()
            self.scroll.setWidgetResizable(True)
            self.scroll.setWidget(self.widget)
            
            self.main_layout = QVBoxLayout()
            self.main_layout.addWidget(self.scroll)
            self.setLayout( self.main_layout) 
            
            self.ly_devices = QVBoxLayout(objectName='ly_devices')
            self.widget.setLayout(self.ly_devices)

     
    def make(self, view: ViewConfig, devices):
        
        #if view.ui_file:
        #    find_ui(view.ui_file)
        container = self.DefaultContainer( )
            
        ui_devices =  list( get_ui_child(devices, container,  view.setup) )
        for dev in ui_devices:
            dev.start()
            dev.append_widget()
            
        return DevicesView(container, ui_devices)

@dataclass
class DevicesView:
    container: QWidget
    ui_devices: List[QtBaseDevice]
    
    def connect_downloader(self, downloader):
         for dev in self.ui_devices:
            dev.connect_downloader(downloader)

    def disconnect_downloader(self):
        for dev in self.ui_devices:
            dev.disconnect_downloader()
    
    def clear(self):
        for dev in self.ui_devices:
            dev.kill()
        self.ui_devices.clear()

    def kill(self):
        self.disconnect_downloader()
        self.clear()
        self.container.setParent(None)
        self.container = None


def get_default_views():
    return {
        'ctrl':ViewConfig(setup = [ViewSetupConfig(widget_kind= 'ctrl')]), 
        'line':ViewConfig(setup = [ViewSetupConfig(widget_kind= 'line')]), 
        'cfg':ViewConfig(setup = [ViewSetupConfig(widget_kind= 'cfg')]) 
        }



@dataclass
class DevicesViewSwitcher:
    children_maker = ViewChildMaker()
    def switch_view(self, qlayout, devices, view, downloader=None):
        devices_view =  self.children_maker.make(view, devices)

        qlayout.addWidget( devices_view.container )
        return devices_view 
    

@dataclass
class ViewConnector(BaseConnector):
    layout: QLayout
    
    views: Dict[str, ViewsConfig] = field(default_factory=get_default_views)
    view_switcher = DevicesViewSwitcher() 
    action_menu_connector = get_connector_class(QAction, Action)() 
    
    def connect(self, widget: QMainWindow, menu: QMenu, devices: List[BaseDevice] ):
        def set_view(view_name:  str):
            self.set_view(widget, devices, view_name)    
        
        view_actions = []
        for view_name in self.views:
                viewAct = QAction(view_name, widget)
                menu.addAction(viewAct)
                action = Action( set_view, [view_name])
                self.action_menu_connector.connect( viewAct, action)
                view_actions.append(action)
        widget.view_actions = view_actions
    
    def refresh(self, widget):
        if widget.downloader:
            if widget.devices_view: 
                widget.devices_view.disconnect_downloader()
                widget.devices_view.connect_downloader( widget.downloader)
    
    def set_view(self, widget, devices, view_name):
        if widget.devices_view:
            widget.devices_view.kill()
         
        widget.devices_view = self.view_switcher.switch_view( self.layout, devices, self.views[view_name])
        if widget.downloader:
            widget.devices_view.connect_downloader( widget.downloader)
        
        



if __name__ == "__main__":
    f = DevicesView([], "ctrl")


    



    

