


from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any, Type

from PyQt5.QtWidgets import QCheckBox, QFrame, QMainWindow, QWidget
from PyQt5 import QtWidgets

from pydevmgr_core import BaseParser, parser
from pydevmgr_core_qt2.getters import QtBoolTextGetter, QtTextGetter
from pydevmgr_core_qt2.style import Style, get_style
from pydevmgr_core_ui import BaseSetter, BaseContainerFeedback, record_setter
from typing import Tuple 
from pydantic import BaseModel

from pydevmgr_core_ui.setter import UiInterface, WidgetDataSetter


@record_setter(QtWidgets.QLineEdit, str)
@record_setter(QtWidgets.QLabel, str)
@dataclass
class QtTextSetter(BaseSetter):
    format: str = "%s"
    parser: Optional[BaseParser] = None
    feedback: Optional[BaseContainerFeedback] =None
    def __post_init__(self):
        if self.parser:
            self.parser = parser(self.parser)
        
    def set(self, widget, value) -> None:
        if self.feedback:
            try:
                value = self.parse(value)
            except Exception as err:
                self.feedback.error(widget, err)
                return 
            else:
                self.feedback.clear(widget, self.format % value)
        else:
            value = self.parse(value)
        
        widget.setText(self.format % value)
    
    def parse(self, value):
        if not self.parser: return value
        return self.parser.parse(value)



@record_setter(QtWidgets.QLineEdit, float)
@record_setter(QtWidgets.QLabel, float)
@dataclass
class QtFloatSetter(QtTextSetter):
    format: str = "%f"
    parser: BaseParser = parser(float)

@record_setter(QtWidgets.QLineEdit, int)
@record_setter(QtWidgets.QLabel, int)
@dataclass
class QtIntSetter(QtTextSetter):
    format: str = "%d"
    parser: BaseParser = parser(int)



@record_setter(QtWidgets.QLineEdit, bool)
@record_setter(QtWidgets.QLabel, bool)
@dataclass
class QtBoolSetter(BaseSetter):
    true_text: str = "[X]"
    false_text: str = "[ ]"
    
    def set( self, widget, value) -> None:
        value = bool(value)
        
        if isinstance(widget, QCheckBox):
            widget.setChecked(value)
        else:
            widget.setText( self.true_text if value else self.false_text )

@record_setter(QtWidgets.QCheckBox, bool)
@dataclass
class QtCheckSetter(BaseSetter):
    def set( self, widget: QCheckBox, test: bool) -> None:
        widget.setChecked( bool(test))



@record_setter(QtWidgets.QComboBox, Enum)
@dataclass
class QtComboEnumSetter(BaseSetter):
    enum: Enum
    offset: int = 0 
    def set(self, widget, value):
        value = self.enum(value)
        index = list(self.enum).index(value)
        widget.setCurrentIndex( index + self.offset)


@record_setter(QtWidgets.QLabel, Enum)
@dataclass
class QtLabelEnumSetter(BaseSetter):
    enum: Enum
    def set(self, widget, value):
        value = self.enum(value)
        widget.setText( value.name )




@dataclass
class QtStyleSwitcher(BaseSetter):
    true_style: str = get_style(Style.SIMILAR)
    false_style: str = get_style(Style.DIFFERENT)
    def set(self, widget: QWidget, test: bool) -> None:
        widget.setStyleSheet( self.true_style if test else self.false_style )


@dataclass
class QtIoSetter(BaseSetter):
    setter: QtTextSetter = QtTextSetter()
    getter: QtTextGetter = QtTextGetter()
    style_switcher: QtStyleSwitcher = QtStyleSwitcher()
    comparator: Callable = lambda x,y: x==y  

    def set(self, widgets: Tuple[QWidget, QWidget],  value) -> None:
        input, output = widgets
        self.setter.set(output, value)
        test = self.comparator(value, self.getter.get(input) )
        self.style_switcher.set(output, test)

    def get(self, widgets: Tuple[QWidget, QWidget]):
        input, _ = widgets
        return self.getter.get(input)
    
    def set_input(self, widgets: Tuple[QWidget, QWidget], value: Any) -> None:
        input, _ = widgets
        self.setter(input, value)


@dataclass
class IoGroup:
    input: Any
    output: Any 

@dataclass
class QtIo(BaseSetter):
    setter: QtTextSetter = QtTextSetter()
    getter: QtTextGetter = QtTextGetter()
    style_switcher: QtStyleSwitcher = QtStyleSwitcher()
    comparator: Callable = lambda x,y: x==y  

    def set(self, widgets: IoGroup,  value) -> None:
        input, output = widgets.input, widgets.output
        
        self.setter.set(output, value)
        test = self.comparator(value, self.getter.get(input) )
        self.style_switcher.set(output, test)

    def get(self, widgets: IoGroup):
        return self.getter.get(widgets.input)
    
    def set_input(self, widgets: IoGroup, value: Any) -> None:
        self.setter(widgets.input, value)



class QtInterface(UiInterface):
    widget: str
    setter: Optional[Callable] = QtTextSetter()
    getter: Optional[Callable] = None 
    builder: Optional[Callable] = None 



@record_setter( QFrame, BaseModel)
@record_setter( QWidget, BaseModel)
@record_setter( QMainWindow, BaseModel)
class QtDataSetter(WidgetDataSetter):
    ...


