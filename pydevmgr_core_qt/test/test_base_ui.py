from pydevmgr_core_qt import * 
from pydevmgr_core import MeanFilterNode, MaxNode, MinNode, DequeNode1, NoiseNode, LocalUtcNode, LocalNode, BaseDevice, Downloader, NodeVar, parser
from pydantic import Field
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5 import  QtCore


class TestWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ly = QVBoxLayout()
        self.setLayout(self.ly)
        
        self.title = QLabel()
        self.title.setText("Hello")
        self.ly.addWidget(self.title)
        
        self.label0 = QLabel()
        self.label0.setText("Hello")
        self.ly.addWidget(self.label0)
        
        self.label1 = QLabel()
        self.label1.setText("Hello")
        self.ly.addWidget(self.label1)
        
        self.label2 = QLabel()
        self.label2.setText("UTC")
        self.ly.addWidget(self.label2)
        
        self.label3 = QLabel()
        self.label3.setText("C")
        self.ly.addWidget(self.label3)
        
        self.go = QPushButton()
        self.go.setText("+1")
        self.ly.addWidget(self.go)
        
        self.go2 = QPushButton()
        self.go2.setText("-1")
        self.ly.addWidget(self.go2)
        
class TestDevice(BaseDevice):
    noise = NoiseNode.prop()        
    utc = LocalUtcNode.prop()
    counter = LocalNode.prop(default=0, parser=parser("Bounded", max=3, min=0))
    
class TestUiLinker(BaseUiLinker):
    Widget = TestWidget
        
    class Data(BaseDevice.Data):
        noise: NodeVar[float] = 0.0
        maxnoise: NodeVar[float] = Field(0.0, node=MaxNode.prop(node="noise"))
        
        utc: NodeVar[str] = ""
        counter: NodeVar[int] = 0
        meancounter: NodeVar[float] = Field(0.0, node=MeanFilterNode.prop(node="counter"))
        
    def init_vars(self):
        self.outputs.noise = self.outputs.Float(self.widget.label0)
        self.outputs.maxnoise = self.outputs.Float(self.widget.label1)
        self.outputs.utc = self.outputs.Str(self.widget.label2)
        self.outputs.counter= self.outputs.Str(self.widget.label3)
        
    def update(self, data):
        self.outputs.noise.set(data.noise)   
        self.outputs.maxnoise.set(data.maxnoise) 
        self.outputs.utc.set( data.utc)
        self.outputs.counter.set( f"{data.counter} {data.meancounter}" )
    
    def feedback(self, er, msg):
        if er:
            print(er, msg)
            self.widget.label3.setStyleSheet(STYLE_DEF.ERROR)
            self.widget.label3.repaint()
        else:
            print("ok")
            self.widget.label3.setStyleSheet(STYLE_DEF.NORMAL)
            self.widget.label3.setStyleSheet("")
            
            
    def setup_ui(self, device, data):
        
        self.widget.title.setText("::: "+data.key)
        
        f = lambda: device.counter.set( data.counter+1)
        action = self.actions.add(f, [], feedback=self.feedback)
        action.connect_button(self.widget.go)
        
        f = lambda: device.counter.set( data.counter-1)
        action = self.actions.add(f, [], feedback=self.feedback)
        action.connect_button(self.widget.go2)
        
        
if __name__=="__main__":
    app = QApplication(sys.argv)
    ul = TestUiLinker()        
    ul.widget.show()
    
    device = TestDevice()
    downloader= Downloader()
    
    c = ul.connect(downloader, device)
    
    timer = QtCore.QTimer()
    timer.timeout.connect(downloader.download)
    timer.start(100)
    
    app.exec_()