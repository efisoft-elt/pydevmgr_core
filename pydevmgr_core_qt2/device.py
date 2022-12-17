

from dataclasses import InitVar, dataclass
from typing import Optional
from PyQt5.QtWidgets import QFrame, QWidget
from pydevmgr_core import Downloader
from pydevmgr_core import BaseDevice
from pydevmgr_core.base.monitor import MonitorConnection, MonitorLink

from pydevmgr_core_qt2.base import  QtMonitor, BaseAppender, BaseRemover
from pydevmgr_core_ui import BaseConnector, Connection



class QtRemover(BaseRemover):
    """ Handled the removel of a widget from its parent """
    def remove(self, widget: QWidget)-> None:
        widget.setParent(None)    


@dataclass
class QtBaseDevice:
    device: BaseDevice
    widget: Optional[QWidget] = None 
    widget_appender: Optional[BaseAppender] = None
    widget_remover: Optional[BaseRemover] = QtRemover()
    monitor: Optional[QtMonitor] = None    
    connector: Optional[BaseConnector] = None
    
    downloader: InitVar[Optional[Downloader]] = None

    Widget = QFrame
    Monitor = QtMonitor
    Connector = BaseConnector
    
       
    def __post_init__(self, downloader):
        if self.widget is None:
            self.widget  = self.Widget()
        if self.monitor is None:
            self.monitor     = self.Monitor()
        if self.connector is None:
            self.connector = self.Connector()

            
        self.link        = MonitorLink(self.monitor, self.widget)
        self.monitor_connection   = MonitorConnection(self.link, self.device, downloader)
        self.connection   = Connection(self.connector, self.widget, self.device)

    def connect_downloader(self, downloader):
        self.monitor_connection.connect_downloader(downloader)
        self.monitor_connection.start()
    
    def disconnect_downloader(self):
        self.connection.disconnect()
        self.monitor_connection.disconnect_downloader() 
    
    def stop(self):
        self.monitor_connection.stop()
        # do something with widget 
    
    def start(self):
        self.monitor_connection.start()
    
    def pause(self):
        self.monitor_connection.pause()

    def resume(self):
        self.monitor_connection.resume()

    def update(self):
        self.link.update()
        
    def show(self):
        self.widget.show()
    
    def append_widget(self):
        if self.widget_appender is None:
            raise ValueError("This QtDevice does not have an appender for its widget")
        return self.widget_appender.append(self.widget)
    
    def remove_widget(self):
        self.widget_remover.remove(self.widget)

    def kill(self):
        self.stop()
        # self.disconnect()
        self.remove_widget()
