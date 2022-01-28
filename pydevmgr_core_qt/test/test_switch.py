from pydevmgr_elt_qt import MotorCtrl
from pydevmgr_elt import Motor
from pydevmgr_core import Downloader
from pydevmgr_core_qt.switch import SwitchLinker


import sys
from PyQt5.QtWidgets import QApplication
from PyQt5 import  QtCore

connect_me = True

if __name__=="__main__":
    app = QApplication(sys.argv)
    devLinker = SwitchLinker()
    devLinker.widget.show()
    downloader = Downloader()
    
    motor = Motor.from_cfgfile("tins/motor1.yml", "motor1", key="motor1")
    
    ctrl = devLinker.connect(downloader, motor)
    
    if connect_me:
        # To refresh the gui we need a timer and connect the download method 
        timer = QtCore.QTimer()
        timer.timeout.connect(downloader.download)
        # 10Hz GUI is nice
        timer.start(100)
        
        motor.connect()
    try:
        app.exec_()
    finally:
        if connect_me:
            motor.disconnect()