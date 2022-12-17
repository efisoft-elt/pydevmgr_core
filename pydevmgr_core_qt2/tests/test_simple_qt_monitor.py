from pydevmgr_core.base.class_recorder import record_class
from pydevmgr_core.base.interface import BaseInterface
from pydevmgr_core.base.monitor import MonitorLink
from pydevmgr_core_qt2.base import QtMonitor
from pydevmgr_core import MonitorDownloader, NodeVar, MonitorConnection, Downloader
from pydevmgr_core.nodes import Value, Counter
from pydantic import BaseModel 
from PyQt5.QtWidgets import QFrame, QLabel, QLayout, QVBoxLayout, QApplication
from PyQt5 import QtCore

import sys 


class MyWidget(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.label = QLabel(text="Hellow")
        self.layout.addWidget( self.label ) 

@record_class
class M(QtMonitor):
    class Config:
        kind: str = "QtMonitor"
        type =  "M"
    def update(self, widget: MyWidget, data, err=None):
        widget.label.setText( str(data.label) )
    
class Data(BaseModel):
    label: NodeVar[str] = ""


class I(BaseInterface):
    label = Counter.Config()

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    i = I()
    m = M() 
    d = Data() 
    
    w = MyWidget()
    w.show()
    

    timer = QtCore.QTimer()
    
    counter = 0
    if True:  
        dl = MonitorDownloader( MonitorLink( m, w, i, d))  
        timer.timeout.connect(dl.download)
    else:
        downloader = Downloader()
        c = MonitorConnection( MonitorLink( m, w, i, d) )
        c.connect(downloader)
        c.start()
        timer.timeout.connect(downloader.download)

    timer.start(100)
    


    app.exec_()
