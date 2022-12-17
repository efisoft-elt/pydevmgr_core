from PyQt5.uic.uiparser import QtWidgets
from pydantic.main import BaseModel
from pydevmgr_core import BaseMonitor, BaseObject
from pydevmgr_core_ui import BaseConnector, record_ui, get_ui_class
from PyQt5.QtWidgets import  QWidget


def record_qt(object_type, kind):
    return record_ui('qt', object_type, kind)

def get_qt_class(object_type, kind):
    return get_ui_class('qt', object_type, kind) 


class QtMonitor(BaseMonitor):
    def setup(self, widget:QWidget, data: BaseModel, obj:BaseObject):
        pass
    
    def start(self, widget:QWidget, data: BaseModel):
        pass

    def error(self, widget: QWidget, err: Exception):
        widget.setEnabled(False)
        print( err)
    
    def clear_error(self, widget: QWidget):
         widget.setEnable(True)
    
    def update(self, widget: QWidget, data: BaseModel):
        pass
    
    def stop(self, widget: QWidget):
        pass
    

class BaseAppender:
    def append(self, widget: QWidget):
        raise NotImplementedError("append")


class BaseRemover:
    def remove(self, widget: QWidget):
        raise NotImplementedError("remove")




         


