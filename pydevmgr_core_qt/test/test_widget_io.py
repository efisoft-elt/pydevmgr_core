from PyQt5.QtWidgets import QApplication
from PyQt5 import  QtCore
from PyQt5.QtWidgets import QLabel
import sys 
import time


from pydevmgr_core_qt.widget_io3 import * 

if __name__=="__main__":
    app = QApplication(sys.argv)
    BoolVal_O.Config()
    
    
    w = QLabel()
    v = BoolVal_O(w)
    
    tic = time.time()
    N = 20000
    for i in range(N):        
        v.set(True)
    toc = time.time()
    print( (toc-tic)/N *1e6) 
    
    tic = time.time()
    for i in range(N):        
        v.set(True)
    toc = time.time()
    print( (toc-tic)/N *1e6) 
    
    tic = time.time()
    for i in range(N):        
        v.set(True)
    toc = time.time()
    print( (toc-tic)/N *1e6) 
    
    tic = time.time()
    for i in range(N):        
        v.set(True)
    toc = time.time()
    print( (toc-tic)/N *1e6) 
    
    
    class BoolLabelOutput(Output):                
        @classmethod
        def accept(cls, w):
            return hasattr(w, "setText") 
        def __init__(self, w, c):
            print("ok")
            def set_output(b):
                t = c.fmt(b)                
                w.setText(t)
            self.set  = set_output              
    
    BoolVal_O.BoolLabelOutput = BoolLabelOutput
    v = BoolVal_O(w)
    
    tic = time.time()
    for i in range(N):        
        v.set(True)
    toc = time.time()
    print( (toc-tic)/N *1e6) 