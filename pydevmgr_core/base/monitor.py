import time
from typing import Callable, Iterable, Optional,Any, Union
from dataclasses import dataclass, field
from pydantic.main import BaseModel
from pydevmgr_core.base.datamodel import DataLink

from pydevmgr_core.base.download import Downloader
from pydevmgr_core.base.base import BaseObject


class EndMonitor(StopIteration):
    pass



class BaseMonitor:
    class Data(BaseModel):
        pass
    
    def start(self, container: Any, data: BaseModel) -> None:
        raise NotImplementedError("start")
    
    def error(self, container: Any, err: Exception):
        """ Executed when an external error occurs """
        pass

    def clear_error(self, container: Any):
        """ Exceuted when external error is cleared """
        pass

    def update(self, 
            container: Any, 
            data: BaseModel
        ) -> None:
        raise EndMonitor
    
    def stop(self, container):
        raise NotImplementedError("stop")
    
    def resume(self):
        pass

    def pause(self):
        pass

@dataclass
class MonitorGroup:
    monitors: Iterable[BaseMonitor] = field(default_factory=list)
    
    class Data(BaseModel):
        pass
    
    def start(self, container: Any, data: BaseModel) -> None:
        for monitor in self.monitors:
            monitor.start(container, data)
    
    def error(self, container: Any, err: Exception):
        """ Executed when an external error occurs """
        for monitor in self.monitors:
            monitor.error(container, err)
    
    def clear_error(self, container: Any):
        """ Exceuted when external error is cleared """
        for monitor in self.monitors:
            monitor.clear_error(container)

    def update(self, 
            container: Any, 
            data: BaseModel
        ) -> None:
        for monitor in self.monitors:
            monitor.update(container, data)
        
    def stop(self, container):
        for monitor in self.monitors:
            monitor.stop(container)
    
    def resume(self):
        for monitor in self.monitors:
            monitor.resume()

    def pause(self):
        for monitor in self.monitors:
            monitor.pause()        




class MonitorLink:
    def __init__(self, 
            monitor: BaseMonitor,
            container: Any, 
            data: Optional[BaseModel] = None
        ) -> None:
        if data is None:
            data = monitor.Data()
        self.data = data 
        self.monitor = monitor
        self.container = container
    
        
    def start(self) -> None:
        self.monitor.start(self.container, self.data)

    def update(self):
        self.monitor.update(self.container, self.data)
    
    def stop(self):
        self.monitor.stop(self.container)

    def resume(self):
        self.monitor.resume()

    def pause(self):
        self.monitor.pause()
    
    def error(self, err):
        return self.monitor.error(self.container, err) 
    
    def clear_error(self):
        return self.monitor.clear_error(self.container)


class MonitorConnection:
    """ Establish a connection between a downloader and a monitor link """ 
    _downloader = None  
    _connection = None        
    _data_link  = None
    _last_download_has_failed = False

    def __init__(self, link: MonitorLink, obj: BaseObject, downloader: Optional[Downloader] = None):              
        self.link = link 
        self.data_link = DataLink(obj, link.data)
        self._downloader = downloader    
       
    def connect_downloader(self, downloader):
        """ Prepare a connection between the downloader and the monitor link  

        The datalink is built as well as feedback methods. 
        Does not do anything but shall be followed by start()  
        """
        self.disconnect_downloader()
        self._downloader = downloader 
       
    def _update(self):
        try:
            self.link.update()
        except EndMonitor:
            self.stop()

    def update(self):
        try:
            self.data_link.download()
        except Exception as er:
            self._last_download_has_failed = True
            self.link.error(er)
        else:
            if self._last_download_has_failed:
                self._last_download_has_failed = False
                self.link.clear_error()
            self._update()

    
    def _update_failure(self, err: Exception):
        try:
            if err is None: 
                self.link.clear_error() 
            else:
                self.link.error(err)
        except EndMonitor:
            self.stop()

    def _link_datalink_and_methods(self):
        if self._connection: self._connection.disconnect()
        
        self._connection = self._downloader.new_connection()

        self._connection.add_datalink( self.data_link) 
        self._connection.add_callback(self._update)
        self._connection.add_failure_callback(self._update_failure)
        self._method_linked = True

    def start(self):
        """ start the monitor and link update method to the downloader """
        self.link.start()
        if self._downloader:
            self._link_datalink_and_methods()
    
    def stop(self):
        """ disconnect to downloader end send stop to monitor """
        self.disconnect_downloader() 
        self.link.stop()
        
    def disconnect_downloader(self):
        """ disconnect method and datalink from the downloader """
        
        if self._connection:
            self._connection.disconnect()
        self._connection = None

    def resume(self):
        """ resume the monitor after it has been paused """
        if not self.data_link:
            raise ValueError("not connected")
        self.link.resume()
        if self._connection: 
            self._link_datalink_and_methods()
    
    def pause(self):
        """ pause the monitor """
        self.disconnect_downloader()
        self.link.pause()


@dataclass 
class MonitorDownloader:
    """ from a MonitorLink download its data and update the monitor """
    def __init__(self, link: MonitorLink, obj: BaseObject, catch_failure=True):
        self.link = link
        
        self.data_link = DataLink( obj, link.data) 
        self.catch_failure = catch_failure 
        
    def start(self):
        self.link.start()
        
    def update(self):
        """ Download nodes and then """
        if self.catch_failure:
            try:
                self.data_link.download()
            except Exception as er:
                self.link.update(er)
            else:
                self.link.update()
        else:
            self.link.update()
        
    def stop(self):
        self.link.stop()

    def resume(self):
        self.link.resume()

    def pause(self):
        self.link.pause()

@dataclass
class MonitorRunner:
    link: Union[MonitorLink, MonitorDownloader]
    period: float = 1.0 
    max_iteration: int = 2**64

    _running_flag = False
    _paused_flag = False
    
    def start(self):
        if self._running_flag:
            raise RuntimeError("this runner is already running")
    
        period = self.period
        max_iteration = self.max_iteration
        link = self.link

        self._running_flag = True

        try:
            link.start()
            i = 0    
            while True:
                if not self._running_flag:
                    break 
                if i>=max_iteration:
                    break
                if self._paused_flag:
                    link.pause()
                    while self._paused_flag and self._running_flag:
                        time.sleep(0.001)
                    link.resume()

                tic = time.time()
                
                try:
                    link.update()
                except EndMonitor:
                    break
                i += 1
                toc = time.time()
                time.sleep( max(period-(toc-tic), 1e-6) ) # This avoid negative sleep time
        finally:
            self._running_flag = False
            link.stop()
    
    def stop(self):
        self._running_flag = False

    def pause(self):
        self._paused_flag = True

    def resume(self):
        self._paused_flag = False 
        
    
if __name__ == "__main__":
    
    class M(BaseMonitor):
        counter = 0 
        # def __init__(self):
        #     super().__init__()
        #     self._counter = 0 
                     
        def start(self, txts, data):
            self.counter = 0
            self._start_time = time.time()
            txts.append("I am starting")

        def update(self, txts, data, error=None):
            if self.counter> 10:
                raise EndMonitor
                
            clock =  time.time() - self._start_time 
            txts.append(f"Iteration {self.counter} {clock}")
            self.counter += 1 

        def stop(self, txts):
            txts.append( "I Have Finished")
    
    txts = []
    runner = MonitorRunner(MonitorLink( M(), txts, BaseModel()),   period=0.1, max_iteration=5)
    runner.start() 
    print( "\n".join(txts) )
    
    from pydevmgr_core import Downloader
    from pydevmgr_core.nodes import Value
    v = Value(value=99)  
    
    downloader = Downloader()
    txts = []
    c = MonitorConnection( MonitorLink( M(), txts, v.Data()), v)
    c.connect_downloader( downloader) 
    c.start()
    downloader.download()
    downloader.download()
    c.stop()
    print( "\n".join(txts) )
    txts.clear() 
    
    d = MonitorDownloader(MonitorLink( M(), txts,  v.Data()), v)
    d.start()
    d.update()
    d.update()
    d.stop()
    
    print( "\n".join(txts) )



