from typing import Dict

from PyQt5.QtWidgets import QAction, QCheckBox, QPushButton, QWidget, QComboBox 
from pydevmgr_core_ui import Action, BaseConnector, record_connector, get_connector_class
from pydevmgr_core_ui.actions import ActionMap, ActionIndex 

@record_connector(QComboBox, ActionIndex)
class QtComboIndexConnector(BaseConnector):
    """ Helper function to link some actions to a QT Combo box 

    Args:
        widget: :class:`PyQt5.QtWidgets.QComboBox`
        actions: :class:`ActionsIndex`
    
    """
    def connect(self, widget: QComboBox, actions: Action):
        widget.currentIndexChanged.connect(actions.call) 
    
    def add_item(self, widget, item, caller=None):
        widget.addItem(item)
        if caller: self.actions.add_caller( caller, widget.count()-1 )
    
    def disconnect(self, widget):
        widget.currentIndexChanged.disconnect()

@record_connector(QComboBox, ActionMap)
class QtComboConnector(BaseConnector):
    """ Helper function to link some actions to a QT Combo box 
    
    Actions map and combo box item are matched by name. 
    The action is triggered when the selected item text is equal 
    to the action map keys.

    Args:
        widget: :class:`PyQt5.QtWidgets.QComboBox`
        actions: :class:`ActionsMap`
    
    """
    def connect(self, widget: QComboBox, actions: ActionMap):
        
        def callback(index):
            actions.call( widget.itemText(index) )
        widget.currentIndexChanged.connect(callback) 
    
    def add_item(self, widget, item, caller=None):
        widget.addItem(item)
        if caller: self.actions.add_caller( caller, widget.count()-1 )
    
    def disconnect(self, widget):
        widget.currentIndexChanged.disconnect()


    
@record_connector(QCheckBox, Action)
class QtCheckBoxConnector(BaseConnector):
    def connect(self, widget: QCheckBox, action: Action):
        widget.stateChanged.connect(action.call)

    def disconnect(self, widget: QCheckBox):
        widget.stateChanged.disconnect()
    
    
@record_connector(QPushButton, Action)     
class QtButtonConnector(BaseConnector):
    def connect(self, widget: QPushButton, action: Action):
        widget.clicked.connect(action.call)

    def disconnect(self, widget: QCheckBox):
        widget.clicked.disconnect()
    

@record_connector(QAction, Action)   
class QtActionMenuConnector(BaseConnector):
    def connect(self, qaction: QAction, action: Action):
        qaction.triggered.connect(action.call)

    def disconnect(self, qaction: QAction):
        qaction.triggered.disconnect()




