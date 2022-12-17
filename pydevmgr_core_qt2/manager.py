


from dataclasses import dataclass
from typing import Callable, List, Optional
from PyQt5.QtWidgets import QAction, QFrame, QGridLayout, QHBoxLayout, QMainWindow, QMenu, QVBoxLayout, QWidget, qApp
from pydevmgr_core_qt2.actions import QtActionMenuConnector
from pydevmgr_core_qt2.base import QtMonitor
from pydevmgr_core_qt2.devices import ViewConnector, get_default_views
from pydevmgr_core.base.manager import BaseManager
from pydevmgr_core.base.monitor import MonitorConnection, MonitorLink
from pydevmgr_core_qt2.view import ViewsConfig
from pydevmgr_core_ui import  BaseConnector, Action, get_connector_class, BaseConnector, Connection, ConnectorGroup


class DeviceLister:
    def list(self, manager):
        return manager.devices


class ViewManagerConnector(BaseConnector):
    """ Connect a manager with a widget for the view menu 

    The widget must have attributes: 
        body_layout QLayout 
        view_menu: QMenu 
        views_config: Dict[str,ViewConfig]
        
    """
    action_menu_connector = get_connector_class(QAction, Action)() 
    device_lister = DeviceLister() 
    
    view_connector = None
    def connect(self, widget: QMainWindow, manager: BaseManager):
        devices = self.device_lister.list(manager)
        self.view_connector = ViewConnector(widget.body_layout, widget.views_config)
        self.view_connector.connect( widget, widget.view_menu, devices)
        self.view_connector.set_view(widget,  devices,  list(widget.views_config)[0] )
    
        self.refresh(widget)

    def refresh(self, widget: QMainWindow):
        self.view_connector.refresh(widget) 

    
    def disconnect(self, widget: QMainWindow):
        self.view_connector.view_switcher.disconnect_downloader()
         

class ManagerWidget(QMainWindow):
    downloader = None
    devices_view = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        top = QWidget()
        bottom = QWidget()
        left = QWidget()
        right = QWidget()
        body = QWidget()
         
        
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        body_layout = QVBoxLayout()


        top.setLayout(top_layout)
        bottom.setLayout(bottom_layout)
        left.setLayout(left_layout)
        right.setLayout(right_layout)
        body.setLayout(body_layout)

        
        main_layout = QGridLayout()
        main = QWidget()
        main.setLayout(main_layout)
        
        main_layout.addWidget( top, 0, 0, 1, 3 )
        main_layout.addWidget( left, 1, 0 )
        main_layout.addWidget( bottom, 2, 0, 1, 3 )
        main_layout.addWidget( right, 1, 2)
        main_layout.addWidget( body, 1, 1)


        self.setCentralWidget(main)
        
        # main_layout = QVBoxLayout()
        # self.setLayout(main_layout)
        # main_layout.addWidget(self.body)
        
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        # Creating menus using a QMenu object
        fileMenu = QMenu("&File", self)
        menuBar.addMenu(fileMenu)
        
        self.resize(750, 1000)
                
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
        
        fileMenu.addAction(exitAct)
        
        self.view_menu = QMenu("&View", self)
        menuBar.addMenu(self.view_menu)
        
        self.menuBar = menuBar
        
        
        self.top = top 
        self.right = right
        self.left = left 
        self.bottom = bottom 
        self.body = body 
        self.main = main 

        self.top_layout = top_layout 
        self.right_layout = right_layout
        self.left_layout = left_layout 
        self.bottom_layout = bottom_layout 
        self.body_layout = body_layout 
        self.main_layout = main_layout 




@dataclass
class QtManagerView:
    manager: BaseManager
    view: str = "ctrl"
    widget: Optional[ManagerWidget] = None 
    
    config: ViewsConfig = ViewsConfig( views=get_default_views())

    device_lister = DeviceLister()
    

    Widget = ManagerWidget
    Monitor = QtMonitor
    Connector = BaseConnector 
    ViewConnector = ViewManagerConnector
    

    def __post_init__(self):
        if self.widget is None:
            self.widget  = self.Widget()
        self.widget.views_config = self.config.views
        self.widget.downloader = None
        
        self.monitor   = self.Monitor()
        self.linker    = MonitorLink(self.monitor, self.widget)
        self.monitor_connection = MonitorConnection(self.linker, self.manager)
        

        self.view_connection = Connection( self.ViewConnector(), self.widget, self.manager)
        self.connection      = Connection( self.Connector(), self.widget, self.manager)
        
        # connector = ConnectorGroup([self.Connector(), self.view_connector])

        # self.connection = Connection(connector, self.widget, self.manager)

    def connect_downloader(self, downloader):
        self.widget.downloader = downloader

        self.view_connection.refresh()
        
        self.monitor_connection.connect_downloader(downloader)
        self.monitor_connection.start()

    def disconnect_downloader(self):
        # self.view_connection.disconnect() 
        self.monitor_connection.disconnect_downloader()

    def set_view(self, view_name:  str):
        self.view_connector.set_view( self.widget, self.device_lister.list(self.manager), view_name)

            
        

    

        






         
    
    
      
