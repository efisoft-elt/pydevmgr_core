from dataclasses import dataclass
from pydevmgr_core_ui import BaseBuilder, record_builder
from PyQt5 import QtWidgets
from enum import EnumMeta

@record_builder(QtWidgets.QComboBox, EnumMeta)
@dataclass
class QtComboEnumBuilder(BaseBuilder):
    enum: EnumMeta
    def build(self, widget):
        for e in self.enum:
            widget.addItem( str(e.name) )
        

