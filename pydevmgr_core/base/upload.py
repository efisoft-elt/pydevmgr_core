from collections import OrderedDict
from .node import NodesWriter, BaseNode
from .download import BaseDataLink

from typing import List, Tuple, Union, Optional, Callable, Any, Dict 
import time 



class UploaderConnection:
    """ Hold a connection to a :class:`Uploader` 
    
    Most likely created by :meth:`Uploader.new_connection` 
    
    Args:
       uploader (:class:`Uploader`) :  parent Uploader instance
       token (Any): Connection token 
    """
    def __init__(self, uploader: "Uploader", token: tuple):
        self._uploader = uploader 
        self._token = token 
        self._child_connections = [] 

    def _check_connection(self):
        if not self.is_connected():
            raise RuntimeError("UploaderConnection has been disconnected from its Uploader")
    
    def _collect_tokens(self, tokens:List[Tuple]) -> None:
        if self._token:
            tokens.append( self._token) 
        for child in self._child_connections:
            child._collect_tokens(tokens) 
            

    def is_connected(self)-> bool:
        """ Return True if the connection is still established """
        if not self._token:
            return False 

        if self._token not in self._uploader._dict_nodes:
            return False 
        return True 


    def disconnect(self) -> None:
        """ disconnect connection from the uploader 
        
        All nodes related to this connection (and not used by other connection) are removed from the
        the downloader queue. 
        Also all callback associated with this connection will be removed from the uploader
        
        """
        tokens = [] 
        self._collect_tokens(tokens)
        self._uploader.disconnect(*tokens)
        self._child_connections = []   
        self._token = None
    
    def new_connection(self) -> "UploaderConnection":
        """ create a new child connection. When the master connection will be disconnect, alll child 
        connection will be disconnected. 
        """
        connection = self._uploader.new_connection() 
        self._child_connections.append( connection )
        return connection 
   
    def add_node(self, node: BaseNode, value: Any) -> None:
        """ Register nodes to be uploaded,  associated to this connection 
        
        Args:
            *nodes :  nodes to be added to the upload queue
        """ 
        self._check_connection() 
        self._uploader.add_node(self._token, node, value)
    
    def add_nodes(self, nodes: Dict[BaseNode,Any]) -> None:
        """ Register nodes to be uploaded associated to this connection 
        
        Args:
            nodes (dict) :  nodes to be added to the upload queue. 
                     A dictionary of node/value pairs
        """
        self._check_connection() 
        self._uploader.add_nodes(self._token, nodes)
    
    def remove_node(self, *nodes) -> None:
        """ remove  any nodes to the downloader associated to this connection 
        
        Note that the node will stay inside the downloader data but will not be updated 
        
        Args:
            *nodes :  nodes to be removed from the download queue
        """ 
        self._check_connection() 
        self._uploader.remove_node(self._token, *nodes)
    
    def add_datalink(self, *datalinks) -> None:
        """ Register datalinks to the downloader associated to this connection 
        
        Args:
            *datalinks :  :class:`DataLink` to be added to the download queue on the associated downloader
        """
        self._check_connection() 
        self._uploader.add_datalink(self._token, *datalinks)        
    
    def remove_datalink(self, *datalinks) -> None:
        """ Remove any given datalinks to the downloader associated to this connection 
        
        Args:
            *datalinks :  :class:`DataLink` to be removed 
        """
        self._check_connection() 
        self._uploader.remove_datalink(self._token, *datalinks)        
    
    def add_callback(self, *callbacks) -> None:
        """ Register callbacks to be executed after each download of the associated downloader 
        
        Args:            
            *callbacks :  callbacks to be added to the queue of callbacks on the associated downloader       
        """
        self._check_connection() 
        self._uploader.add_callback(self._token, *callbacks)
    
    def remove_callback(self, *callbacks) -> None:
        """ Remove any of given callbacks of the associated downloader 
        
        Args:            
            *callbacks :  callbacks to be remove 
        """
        self._check_connection() 
        self._uploader.remove_callback(self._token, *callbacks)
    
    def add_failure_callback(self, *callbacks) -> None:
        """ Register callbacks to be executed after each download of the associated downloader 
        
        Args:            
            *callbacks :  failure callbacks to be added to the queue of callbacks on the associated downloader       
        """
        self._check_connection() 
        self._uploader.add_failure_callback(self._token, *callbacks)
        
    def remove_failure_callback(self, *callbacks) -> None:
        """ Remove any given callbacks of the associated downloader 
        
        Args:            
            *callbacks :  failure callbacks to be removed 
        """
        self._check_connection() 
        self._uploader.remove_failure_callback(self._token, *callbacks)







class Uploader:
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
        
        if node_dict_or_datalink is None:
            node_values = {}
            datalinks = [] 
        elif isinstance(node_dict_or_datalink, BaseDataLink):
            datalinks = [node_dict_or_datalink]
            node_values = {}
        else:
            node_values = node_dict_or_datalink
            datalinks = []
            
        
        self._dict_nodes =OrderedDict([(Ellipsis,node_values)])
        self._dict_datalinks = OrderedDict([(Ellipsis, datalinks)])
            
        callbacks, failure_callbacks = [], [] # !TODO implement
        self._dict_callbacks = OrderedDict([(Ellipsis,callbacks)])
        self._dict_failure_callbacks = OrderedDict([(Ellipsis,failure_callbacks)])

        self._rebuild_nodes()
        self._rebuild_datalinks()
        self._rebuild_callbacks()
        self._rebuild_failure_callbacks()
        # self.node_values = node_values 

        self.datalink = datalinks[0] if datalinks else None
        self.callback = callback
        self._next_token = 1

    def _rebuild_nodes(self):
        nodes: Dict[BaseNode,Any] = {}
        for nds in self._dict_nodes.values():
            nodes.update(nds)

        # for dls in self._dict_datalinks.values():
        #     for dl in dls:
        #         dl._upload_to( nodes )
        #         nodes.update(dl.wnodes)
                                
        self.node_values = nodes
    def _rebuild_datalinks(self):
        datalinks = set()
        for dls in self._dict_datalinks.values():
            datalinks.update(dls)
        self.datalinks = datalinks 

    def _rebuild_callbacks(self):
        callbacks = set()
        for clbc in self._dict_callbacks.values():
            callbacks.update(clbc)
        self._callbacks = callbacks
    
    def _rebuild_failure_callbacks(self):
        callbacks = set()
        for clbc in self._dict_failure_callbacks.values():
            callbacks.update(clbc)
        self._failure_callbacks = callbacks

    def new_token(self) -> tuple:
        token = id(self), self._next_token
        self._dict_nodes[token] =  {}
        self._dict_datalinks[token] = set()
        self._dict_callbacks[token] = set()
        self._dict_failure_callbacks[token] = set()

        self._next_token += 1
        return token 
    
    def new_connection(self) -> UploaderConnection:
        """ return an :class:`UploaderConnection` to handle uploader connection """
        return UploaderConnection(self, self.new_token() )

    def disconnect(self, *tokens: Tuple[Tuple]) -> None:
        """ Disconnect the iddentified connection 
        
        All the nodes used by the connection (and not by other connected app) will be removed from the upload queue of nodes.
        Also all callback associated with this connection will be removed from the uploader 
                 
        Args:
            *tokens : Token returned by :func:`Uploader.new_token`
        """
        for token in tokens:
            if token is Ellipsis:
                raise ValueError('please provide a real token')
            try:
                self._dict_nodes.pop(token)
                self._dict_datalinks.pop(token)
                self._dict_callbacks.pop(token)
                self._dict_failure_callbacks.pop(token)
            except KeyError:
                pass
     
        self._rebuild_nodes()
        self._rebuild_datalinks()
        self._rebuild_callbacks()
        self._rebuild_failure_callbacks()
    
    def add_node(self, token: tuple, node: BaseNode, value: Any)-> None:
        """ register a single node/value pair to the uploader """
        self.add_nodes( token , {node:value})


    def add_nodes(self, token: tuple, nodes: Dict[BaseNode, Any]) -> None:
        """ Register nodes to be uploader for an iddentified app
        
        Args:
            token: a Token returned by :func:`Uploader.new_token` 
                   ``add_node(...,node1, node2)`` can also be used, in this case nodes will be added
                   to the main pool of nodes and cannot be removed from the uploader 
            nodes (Dict): dictionary of node/value pairs to be uploaded
        """
               
        self._dict_nodes[token].update(nodes)
        self._rebuild_nodes()
    
    def remove_node(self, token: tuple, *nodes) -> None:
        """ Remove node from the upload queue
    
        if the node is not in the queueu nothing is done or raised
        
        
        Args:
            token: a Token returned by :func:`Downloader.new_token`                  
            *nodes :  nodes to be removed 
        """   
        for node in nodes:
            try:
                self._dict_nodes[token].pop(node)
            except KeyError:
                pass 
        self._rebuild_nodes()

    def add_datalink(self, token: tuple, *datalinks) -> None:
        """ Register a new datalink
        
        Args:
            token: a Token returned by :func:`Uploader.new_token`
                ``add_datalink(...,dl1, dl2)`` can also be used, in this case they will be added
                to the main pool of datalinks and cannot be remove from the downloader   
            *datalinks :  :class:`DataLink` to be added to the download queue, associated to the token 
        """             
        self._dict_datalinks[token].update(datalinks)
        self._rebuild_datalinks()
    
    
    def remove_datalink(self, token: tuple, *datalinks) -> None:
        """ Remove a datalink from a established connection
        
        If the datalink is not in the queueu nothing is done or raised
        
        Args:
            token: a Token returned by :func:`Uploader.new_token`
            *datalinks :  :class:`DataLink` objects to be removed         
        """
        for dl in  datalinks:
            try:
                self._dict_datalinks[token].remove(dl)
            except KeyError:
                pass 
        self._rebuild_datalinks()
    
    def add_callback(self, token: tuple, *callbacks) -> None:   
        """ Register callbacks to be executed after each upload 
        
        The callback must have the signature f(), no arguments.
        
        Args:
            token: a Token returned by :func:`Uploader.new_connection`
            *callbacks :  callbacks to be added to the queue of callbacks, associated to the app
        
        """ 
        self._dict_callbacks[token].update(callbacks)
        self._rebuild_callbacks()
    
    def remove_callback(self, token: tuple, *callbacks) -> None:   
        """ Remove callbacks 
        
        If the callback  is not in the queueu nothing is done or raised
        
        Args:
            token: a Token returned by :func:`Uploader.new_token`
            *callbacks :  callbacks to be removed 
        
        """
        for c in callbacks:
            try:
                self._dict_callbacks[token].remove(c)
            except KeyError:
                pass 
        self._rebuild_callbacks()
    
    
    def add_failure_callback(self, token: tuple, *callbacks) -> None:  
        """ Add one or several callbacks to be executed when a download failed 
        
        When ever occur a failure (Exception during upload) ``f(e)`` is called with ``e`` the exception. 
        If a upload is successfull **after** a failure ``f(None)`` is called one time only, this allow 
        to clear an error state in the app.
                
        Args:
            token: a Token returned by :func:`Uploader.new_token`
            *callbacks: callbacks to be added to the queue of failure callbacks, associated to the app
        
        """ 
        self._dict_failure_callbacks[token].update(callbacks)
        self._rebuild_failure_callbacks()
    
    def remove_failure_callback(self, token: tuple, *callbacks) -> None:  
        """ remove  one or several failure callbacks 
        
        If the callback  is not in the queue nothing is done or raised
        
        Args:
            token: a Token returned by :func:`Uploader.new_token`
            *callbacks :  callbacks to be removed         
        """ 
        for c in callbacks:
            try:
                self._dict_failure_callbacks[token].remove(c)
            except KeyError:
                pass         
        self._rebuild_failure_callbacks()
    

    def __has__(self, node):
        return node in self._node_values
        
    def upload(self) -> None:
        """ upload the linked node/value dictionaries """
        for dl in self.datalinks:
            dl._upload_to(self.node_values)
        # if self.datalink:
        #     self.datalink._upload_to(self.node_values)
        try: 
            NodesWriter(self.node_values).write() 
        except Exception as e:
            self._did_failed_flag = True

            if self._failure_callbacks:
                for func in self._failure_callbacks:
                    func(e)
            else:
                raise e 
        else:
            if self._did_failed_flag:
                self._did_failed_flag = False
                for func in self._failure_callbacks:                    
                    func(None)
                
            for func in self._callbacks:
                func()
                  
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
