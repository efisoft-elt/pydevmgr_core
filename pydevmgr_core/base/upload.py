from collections import OrderedDict
from .node import NodesWriter, BaseNode
from .download import BaseDataLink, DownloadInput, DownloadInputs , Token, Callback, _BaseDownloader, StopDownloader

from typing import List, Tuple, Union, Optional, Callable, Any, Dict 
from dataclasses import dataclass, field 
import time 
import weakref 

@dataclass
class UploadInput(DownloadInput):
    nodes: Dict[BaseNode, Any] = field(default_factory=dict) 
    
    def add_node(self, node: BaseNode, value: Any)->None:
        self.nodes[node] = value 

    def add_nodes(self, nodes: Dict[BaseNode,Any]):
        self.nodes.update( nodes )

    def remove_node(self, *nodes):
        for node in nodes:
            try:
                self.nodes.pop(node)
            except KeyError:
                pass 


@dataclass 
class UploadInputs(DownloadInputs):

    def new_input(self, token: Token):
        self.connections[token] = UploadInput() 
        return self.connections[token]

    
    def build_nodes(self,
            tokens:Optional[List[Token]] = None  
        )-> None:
        nodes = {}
        for connection in self.iter_connection(tokens):
            nodes.update(connection.nodes)
       
        return nodes

    def build_uploader(self, 
         tokens:Optional[List[Token]] = None, 
        )-> Tuple[List[BaseNode], Callable]:
        
        nodes= self.build_nodes( tokens )
        datalinks = self.build_datalinks( tokens ) 
        callbacks = self.build_callbacks( tokens )
        failure_callbacks = self.build_failure_callbacks( tokens )
        
        def upload(did_failed=False):
            for dl in datalinks:
                dl._upload_to(nodes)

            try:
                NodesWriter(nodes).write()
                
            except Exception as e:
                did_failed = True
    
                if failure_callbacks:
                    for func in failure_callbacks:
                        func(e)
                else:
                    raise e 
            else:
                if did_failed:
                    did_failed  = False
                    for func in failure_callbacks:                    
                        func(None)
                    
                for func in callbacks:
                    func()

               
                return did_failed
        return nodes, upload        


class _BaseUploader(_BaseDownloader):
    def add_node(self, node, value) -> None:
        """ Register node to be downloaded for an iddentified app
        
        Args:
            *nodes :  nodes to be added to the download queue, associated to the app
        """
        self._check_connection() 
        self.inputs[self._token].add_node(node, value) 
        self._rebuild()

    def add_nodes(self, nodes: Dict[BaseNode,Any]) -> None:
        """ Register node to be downloaded for an iddentified app
        
        Args:
            *nodes :  nodes to be added to the download queue, associated to the app
        """
        self._check_connection() 
        self.inputs[self._token].add_nodes(nodes) 
        self._rebuild()

    def run(self, 
            period: float =1.0, 
            stop_signal: Callable =lambda : False, 
            sleepfunc: Callable =time.sleep
        ) -> None:
        """ run the upload indefinitely or when stop_signal return True 
        
        Args:
            period (float, optional): period between downloads in second
            stop_signal (callable, optional): a function returning True to stop the loop or False to continue
            
        """
        try:
            while not stop_signal():
                s_time = time.time()
                self.upload()
                sleepfunc( max( period-(time.time()-s_time), 0))
        except StopDownloader: # any downloader call back can send a StopDownloader to stop the runner 
            return 
            
    def runner(self, 
        period: float =1.0, 
        stop_signal: Callable =lambda : False, 
        sleepfunc: Callable =time.sleep
        ) -> Callable: 
        """ Create a function to run the download in a loop 
        
        Usefull to define a Thread for instance
        
        Args:
            period (float, optional): period between downloads in second
            stop_signal (callable, optional): a function returning True to stop the loop or False to continue
        
                
        """       
        def run_func():
            self.run(period=period, sleepfunc=sleepfunc, stop_signal=stop_signal)
        return run_func
   


class UploaderConnection(_BaseUploader):
    """ Hold a connection to a :class:`Uploader` 
    
    Most likely created by :meth:`Uploader.new_connection` 
    
    Args:
       uploader (:class:`Uploader`) :  parent Uploader instance
       token (Any): Connection token 
    """
    _did_failed_flag = False 
    def __init__(self, uploader: "Uploader", token: tuple):
        self._uploader = uploader 
        self._token = token 
        self._child_connections = [] 
        self.inputs = uploader.inputs 

    def _check_connection(self):
        if not self.is_connected():
            raise RuntimeError("UploaderConnection has been disconnected from its Uploader")
    
    def _collect_tokens(self, tokens:List[Tuple]) -> None:
        if self._token:
            tokens.append( self._token) 
        for child in self._child_connections:
            child._collect_tokens(tokens) 
    

    def _get_parent(self):
        return None

    def _rebuild(self):
        tokens = []
        self._collect_tokens( tokens )
        self._nodes, self._upload_func = self.inputs.build_uploader( tokens )
        parent = self._get_parent()
        if parent:
            parent._rebuild()

    def __has__(self, node):
        return node in self._nodes

    def is_connected(self)-> bool:
        """ Return True if the connection is still established """
        if not self._token:
            return False 
        return self.inputs.has_token(self._token) 
        
    def upload(self) -> None:
        """ upload the linked node/value dictionaries """
        self._did_failed_flag = self._upload_func( self._did_failed_flag )

    def disconnect(self) -> None:
        """ disconnect connection from the uploader 
        
        All nodes related to this connection (and not used by other connection) are removed from the
        the downloader queue. 
        Also all callback associated with this connection will be removed from the uploader
        
        """
        tokens = [] 
        self._collect_tokens(tokens)
        for token in tokens:
            try:
                self.inputs.del_input(token)
            except KeyError:
                pass

        self._child_connections = [] 
        self._token = None
        def upload(data, flag):
            raise ValueError("Disconnected")
        self._nodes, self._upload_func = [] , upload 
        parent = self._get_parent()
        if parent:
            parent._rebuild()
    
    def new_connection(self) -> "UploaderConnection":
        """ create a new child connection. When the master connection will be disconnect, alll child 
        connection will be disconnected. 
        """
        connection = self._uploader.new_connection() 
        self._child_connections.append( connection )
        connection._get_parent = weakref.ref( self )
       
        return connection 
       


class Uploader(_BaseUploader):
    """ An uploader object to upload data to the PLC 
    
    The values to upload is defined in a dictionary of node/value pairs. 
    
    Not sure their is a strong use case for this. Maybe if pydevmgr is used as server instead of client 
    
    Args:
        node_dict_or_datalink (dict, :class:`DataLink`):
             Dictionary of node/value pairs like ``{ motor.cfg.velocity : 4.3 }``
             Or a :class:`pydevmgr_core.DataLink` object.  
        callback (callable, optional): callback function after each upload
    
    Example:
        
    ::
    
        >>> values  = {mgr.motor1.velocity: 1.0, mgr.motor2.velocity: 2.0}
        >>> uploader = Uploader(values)
        >>> t = Thread(target=uploader.runner)
        >>> t.start()
        >>> uploader[mgr.motor1.velocity] = 1.4 # will be uploaded at next trhead cycle 
    
    ::
    
        from pydevmgr_elt import DataLink, NodeVar
        from pydantic import BaseModel 
        
        class Config(BaseModel):
            backlash: NodeVar[float] = 0.0
            disable: NodeVar[bool] = False
        
        >>> conf = Config()
        >>> Uploader( DataLink(mgr.motor1.cfg, conf) ).upload()
            
    .. seealso::
    
       :func:`upload`:  equivalent to Uploader(node_values).upload() 
       
       
    """
    _did_failed_flag = False

    def __init__(self, 
          node_dict_or_datalink: Union[Dict[BaseNode,Any], BaseDataLink, None] = None, 
          callback: Optional[Callable] = None
        ) -> None:
        
        
        self._token = Ellipsis
        self.inputs = UploadInputs()
        main_input = self.inputs.new_input( self._token ) 
        
        

        if node_dict_or_datalink:
            if isinstance(node_dict_or_datalink, BaseDataLink):
                main_input.add_datalink( node_dict_or_datalink) 
            else:
                main_input.add_nodes( node_dict_or_datalink)
            
        if callback:
            main_input.add_callback( callback )
            

        self._rebuild()        # self.node_values = node_values 
        self._next_token = 1

    def _rebuild(self):
        self._nodes, self._upload_func = self.inputs.build_uploader()
    
    def _check_connection(self):
        pass 
    
    def __has__(self, node):
        return node in self._nodes

    def new_token(self) -> tuple:
        token = Token(id(self), self._next_token)
        self.inputs.new_input( token ) 
        self._next_token += 1
        return token
          
    def new_connection(self) -> UploaderConnection:
        """ return an :class:`UploaderConnection` to handle uploader connection """
        connection = UploaderConnection(self, self.new_token() )
        connection._get_parent = weakref.ref(self)
        return connection 
    
            
    def upload(self) -> None:
        """ upload the linked node/value dictionaries """
        self._did_failed_flag = self._upload_func( self._did_failed_flag )

    def run(self, 
          period: float = 1.0, 
          stop_signal: Callable = lambda : False, 
          sleepfunc:  Callable = time.sleep
        ) -> None:
        """ Run the upload infinitly or until stop_signal is True 
        
        Args:
            period (float, optional): period of each upload cycle
            stop_signal (callable, optional): A function called at each cycle, if True the loop is break
                       and run returns    
        """
        while not stop_signal():
            s_time = time.time()
            self.upload()
            sleepfunc( max( period-(time.time()-s_time), 0))

    def runner(self, 
          period: float = 1.0, 
          stop_signal: Callable = lambda : False, 
          sleepfunc:  Callable = time.sleep
        ) -> Callable:
        """ return a function to updload 
        
        this is designed in particular to be used in a target Thread
        
        Args:
            period (float, optional): period of each upload cycle
            stop_signal (callable, optional): A function called at each cycle, if True the loop is break
                       and run returns
        
        Example:
            
            ::
            
                >>> values  = {mgr.motor1.velocity: 1.0, mgr.motor2.velocity: 2.0}
                >>> uploader = Uploader(values)
                >>> t = Thread(target=uploader.runner)
                >>> t.start()
                >>> values[mgr.motor1.velocity] = 1.2 # will be updated at next thread cycle
                               
        """           
        def run_func():
            self.run( period=period, sleepfunc=sleepfunc, stop_signal=stop_signal)
        return run_func
    


def upload(node_dict_or_datalink : Union[Dict[BaseNode,Any], BaseDataLink] ) -> None:
    """ write node values to the remotes
    
    Args:
        node_dict_or_datalink (dict):
             Dictionary of node/value pairs like  ``{ motor.cfg.velocity : 4.3 }``
             Or a :class:`pydevmgr_core.DataLink` object.  
                
    .. note:: 
        
        The input dictionary has pairs of node/value and not node.key/value      
    """
    NodesWriter(node_dict_or_datalink).write()    
