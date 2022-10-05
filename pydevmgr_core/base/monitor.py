import time
from typing import Callable, Optional,Any
from dataclasses import dataclass
from pydantic.main import BaseModel
from pydevmgr_core.base.datamodel import DataLink

from pydevmgr_core.base.download import Downloader
from pydevmgr_core.base.base import BaseObject


class EndMonitor(StopIteration):
    pass

class BaseMonitor(BaseObject):
    class Config(BaseObject.Config):
        kind: str = "Monitor"

    class Data(BaseModel):
        pass
    
    def setup(self, container: Any, data: BaseModel, obj: Optional[BaseObject]):
        pass 

    def start(self, container: Any, data: BaseModel) -> None:
        raise NotImplementedError("start")
    
    def update(self, 
            container: Any, 
            data: BaseModel, 
            error: Optional[Exception] = None
        ) -> None:
        raise EndMonitor
    
    def stop(self, conatainer):
        raise NotImplementedError("stop")
    
    def resume(self):
        pass

    def pause(self):
        pass

class MonitorLinker:
    def __init__(self, 
            monitor: BaseMonitor,
            container: Any, 
            obj: BaseObject,
            data: BaseModel= None
        ) -> None:
        if data is None:
            data = monitor.Data()
        self.data = data 
        self.obj = obj 
        self.monitor = monitor
        self.container = container
        
        self.monitor.setup(self.container, self.data, self.obj)  
    
    def data_link(self):
        return DataLink( self.obj, self.data)
    
    def start(self) -> None:
        self.monitor.start(self.container, self.data)

    def update(self, error: Optional[Exception] = None):
        self.monitor.update(self.container, self.data, error)
    
    def stop(self):
        self.monitor.stop(self.container)

    def resume(self):
        self.monitor.resume()

    def pause(self):
        self.monitor.pause()


class MonitorConnection:
    """ Establish a connection between a downloader and a monitor linker """ 
    _downloader = None  
    _connection = None        
    _data_link = None
    _update_callback = None
    _update_failure_callback = None

    def __init__(self, linker):              
        self.linker = linker 
    
    def connect(self, downloader_or_connection):
        """ Prepare a connection between the downloader and the monitor linker  

        The datalink is built as well as feedback methods. 
        Connect does not do anything but shall be followed by start()  
        """
        self.disconnect()
        
        if isinstance( downloader_or_connection , Downloader):
            self._downloader = downloader_or_connection
            self._connection = downloader_or_connection.new_connection() 
        else:
            self._downloader = None
            self._connection = downloader_or_connection 
        
        def update():
            try:
                self.linker.update()
            except EndMonitor:
                self.disconnect()
                self.linker.stop()
        def update_failure(err):
            try:
                self.linker.update(err)
            except EndMonitor:
                self.disconnect()
                self.linker.stop()

        self._data_link = self.linker.data_link()
        self._update_callback = update 
        self._update_failure_callback = update_failure

    def _link_datalink_and_methods(self):
        if self._downloader:
            self._connection = self._downloader.new_connection()
        
        self._connection.add_datalink( self._data_link) 
        self._connection.add_callback(self._update_callback)
        self._connection.add_failure_callback(self._update_failure_callback)


    def start(self):
        """ start the monitor and link update method to the downloader """
        if not self._data_link:
            raise ValueError("not connected")

        self.linker.start()
        self._link_datalink_and_methods()
    
    def stop(self):
        """ disconnect to downloader end send stop to monitor """
        self.disconnect() 
        self.linker.stop()
        
    def disconnect(self):
        """ disconnect method and datalink from the downloader """
        if self._downloader:
            self._connection.disconnect()
            self._connection = None
        else:
            if self._data_link:
                self._connection.remove_datalink(self._data_link)
            if self._update_callback:
                self._connection.remove_callback( self._update_callback)
            if self._update_failure_callback:
                self._connection.remove_failure_callback( self._update_failure_callback ) 

    def resume(self):
        """ resume the monitor after it has been paused """
        if not self.data_link:
            raise ValueError("not connected")
        self.linker.resume()
        self._link_datalink_and_methods()
    
    def pause(self):
        """ pause the monitor """
        self.disconnect()
        self.linker.pause()


@dataclass 
class MonitorDownloader:
    """ from a MonitorLinker download its data and update the monitor """
    def __init__(self, linker: MonitorLinker, catch_failure=True):
        self.linker = linker
        self.data_link = linker.data_link()
        self.catch_failure = catch_failure 
        
    def start(self):
        self.linker.start()
        
    def download(self):
        if self.catch_failure:
            try:
                self.data_link.download()
            except Exception as er:
                self.linker.update(er)
            else:
                self.linker.update()
        else:
            self.linker.update()
        
    def stop(self):
        self.linker.stop()

    def resume(self):
        self.linker.resume()

    def pause(self):
        self.linker.pause()

@dataclass
class MonitorRunner:
    linker: MonitorLinker
    period: float = 1.0 
    max_iteration: int = 2**64

    _running_flag = False
    _paused_flag = False
    
    def start(self):
        if self._running_flag:
            raise RuntimeError("this runner is already running")
    
        period = self.period
        max_iteration = self.max_iteration
        linker = self.linker

        self._running_flag = True

        try:
            linker.start()
            i = 0    
            while True:
                if not self._running_flag:
                    break 
                if i>=max_iteration:
                    break
                if self._paused_flag:
                    linker.pause()
                    while self._paused_flag and self._running_flag:
                        time.sleep(0.001)
                    linker.resume()

                tic = time.time()
                
                try:
                    linker.update()
                except EndMonitor:
                    break
                i += 1
                toc = time.time()
                time.sleep( max(period-(toc-tic), 1e-6) ) # This avoid negative sleep time
        finally:
            self._running_flag = False
            linker.stop()
    
    def stop(self):
        self._running_flag = False

    def pause(self):
        self._paused_flag = True

    def resume(self):
        self._paused_flag = False 
        
    
if __name__ == "__main__":
    
    class M(BaseMonitor):
        def __init__(self):
            super().__init__()
            self._counter = 0 
        def setup(self, txts, data, obj):
            txts.append(f"I am using {obj}")
                    
        def start(self, txts, data):
            self._counter = 0
            self._start_time = time.time()
            txts.append("I am starting")

        def update(self, txts, data, error=None):
            if self._counter> 10:
                raise EndMonitor
                
            clock =  time.time() - self._start_time 
            txts.append(f"Iteration {self._counter} {clock}")
            self._counter += 1 

        def stop(self, txts):
            txts.append( "I Have Finished")
    
    txts = []
    runner = MonitorRunner(MonitorLinker( M(), txts, BaseObject()) , period=0.1, max_iteration=5)
    runner.start() 
    print( "\n".join(txts) )

    from pydevmgr_core import Downloader
    from pydevmgr_core.nodes import Value
    v = Value(value=99)  
    
    downloader = Downloader()
    txts = []
    c = MonitorConnection( MonitorLinker( M(), txts, v, v.Data()) )
    c.connect( downloader) 
    c.start()
    downloader.download()
    downloader.download()
    c.stop()
    print( "\n".join(txts) )
    txts.clear() 
    
    d = MonitorDownloader(   MonitorLinker( M(), txts, v, v.Data()) )
    d.start()
    d.download()
    d.download()
    d.stop()
    
    print( "\n".join(txts) )



