


from dataclasses import dataclass
from typing import Any, Optional, Type
from PyQt5 import QtWidgets 
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFrame, QMainWindow, QWidget
from pydantic.main import BaseModel
from pydevmgr_core_ui import BaseContainerFeedback, BaseGetter, record_getter 

from valueparser import BaseParser, parser
from enum import Enum, EnumMeta

from pydevmgr_core_ui.getter import WidgetDataGetter



@record_getter(QtWidgets.QLineEdit, str) 
@record_getter(QtWidgets.QLabel, str) 
@dataclass
class QtTextGetter(BaseGetter):
    parser: Optional[BaseParser] = None
    feedback: Optional[BaseContainerFeedback] = None
    def __post_init__(self):
        if self.parser:
            self.parser = parser(self.parser)
    
    def get(self, widget: QWidget):

        value = widget.text()
        
        if self.parser:
            try: 
                value = self.parser.parse(value)
            except Exception as er:
                if self.feedback:

                   self.feedback.error(widget, er) 
                raise er # error should be raised anyway 
            else:
                if self.feedback:
                    self.feedback.clear(widget, "") 
        return value 



@record_getter(QtWidgets.QLineEdit, float) 
@record_getter(QtWidgets.QLabel, float) 
@dataclass
class QtFloatGetter(QtTextGetter):
    parser: Optional[BaseParser] = parser(float)
    
def get_func(getter: BaseGetter, widget: QWidget):
    def get():
        return getter.get(widget)
    return get 

@record_getter(QtWidgets.QLineEdit, int) 
@record_getter(QtWidgets.QLabel, int) 
@dataclass
class QtIntGetter(QtTextGetter):
    parser: Optional[BaseParser] = parser(int)


@record_getter(QtWidgets.QLineEdit, bool) 
@record_getter(QtWidgets.QLabel,  bool)    
@dataclass
class QtBoolTextGetter(BaseGetter):
    true_text: str = "[X]"
    false_text: str = "[ ]"

    def get(self,  widget: QWidget):
        return widget.text().strip() == self.true_text 


@record_getter(QtWidgets.QCheckBox, bool)
@dataclass
class QtBoolCheckBoxGetter(BaseGetter):
    def get(self, widget: QCheckBox):
        return widget.isChecked()


class _EmptyDefault:
    pass
@record_getter(QtWidgets.QComboBox, Enum)
@dataclass
class QtComboEnumGetter(BaseGetter):
    enum: Enum
    default: Any = _EmptyDefault 
    def get(self, widget :QComboBox):
        index = widget.currentIndex()
        member = widget.itemText(index)
        try:
            val = getattr( self.enum, member)
        except AttributeError:
            if self.default == _EmptyDefault:
                raise ValueError(f" item {member} is not a member of {self.enum}")
            else:
                val = self.default
        return val      





@record_getter( QFrame, BaseModel)
@record_getter( QWidget, BaseModel)
@record_getter( QMainWindow, BaseModel)
class QtDataGetter(WidgetDataGetter):
    default_getter = QtTextGetter()

