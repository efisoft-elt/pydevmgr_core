
from dataclasses import dataclass
from PyQt5.QtWidgets import QWidget

from .style import Style, get_style
from pydevmgr_core_ui import BaseContainerFeedback, BaseFeedback 
from pydevmgr_core import RpcError


@dataclass
class QtChangeStyleContainerFeedback(BaseContainerFeedback):
    ok_style: str = get_style(Style.GOOD_VALUE)
    error_style: str = get_style(Style.BAD_VALUE)
        
    def error(self, widget: QWidget, err: Exception):
        widget.setStyleSheet(self.error_style)
    
    def clear(self, widget, msg):
         widget.setStyleSheet(self.ok_style)


@dataclass
class QtTextFeedback(BaseFeedback):
    widget: QWidget
    ok_style: str = get_style(Style.OK)
    error_style: str = get_style(Style.ERROR)

    def error(self, err):
        self.widget.setText(str(err))
        self.widget.setStyleSheet(self.error_style)
     
    def clear(self, msg):
        self.widget.setText(msg)
        self.widget.setStyleSheet(self.ok_style)


