from dataclasses import dataclass, field

from pydevmgr_core.base.vtype import nodedefault, nodetype
from .node import NodesReader, BaseNode
from .base import  BaseObject


import time
from collections import  OrderedDict, namedtuple

from typing import Any, Dict, Iterable, List, Tuple, Union, Optional, Callable, Set
import weakref 

Callback = namedtuple("Callback", ["func", "priority"])
Token = namedtuple("Token", ["id", "number"])

@dataclass 
class DownloadInfo:
    error: Optional[Exception] = None 
    start_time: float = 0.0 
    end_time: float = 0.0 
    n_nodes: int = 0


class DataView:
    def __init__(self, 
            data: Dict[BaseNode,Any], 
            prefix: Optional[Union[str, BaseObject]] = None
          ) -> None:
        self._data = data
        if prefix is None:
            prefix = ""
        if not isinstance(prefix, str):
            prefix = prefix.key 
        
        if not prefix:
            key_lookup = {n.key:n for n in data if hasattr(n, "key") }
        else:                    
            key_lookup = {}
            pref = prefix+"."
            lp = len(pref)
            for n in data:
                if hasattr(n, "key") and n.key.startswith(pref):
                    key_lookup[n.key[lp:]] = n
        
        self._key_lookup = key_lookup    
    
    def __repr__(self):
        return repr({k:self._data[n] for k,n in self._key_lookup.items() })
    
    def __str__(self):
        return str({k:self._data[n] for k,n in self._key_lookup.items() })
        
    def __getitem__(self, item):
        return self._data[self._key_lookup[item]]
    
    def __setitem__(self, item, value):
        self._data[self._key_lookup[item]] = value
    
    def __delitem__(self, item):
        del self._data[self._key_lookup[item]]
    
    def __getattr__(self, attr):
        return self._data[self._key_lookup[attr]]
    
    def __has__(self, item):
        return item in self._key_lookup
    
    def update(self, __d__={}, **kwargs) -> None:
        for k,v in dict(__d__, **kwargs).iteritems():
            self._data[self._key_lookup[k]] = v
    
    def pop(self, item) -> Any:
        """ Pop an item from the root data ! """
        return self._data.pop(self._key_lookup[item])    
    
    def popitem(self, item) -> Any:
        """ Pop an item from the root data ! """
        return self._data.popitem(self._key_lookup[item])  
    
    def keys(self) -> Iterable:
        """ D.keys() ->iterable on D's root keys with matching prefix
        
        Shall be avoided to use in a :class:`Prefixed` object
        """
        return self._key_lookup.__iter__()
    
    def items(self) -> Iterable:
        for k,n in self._key_lookup.items():
            yield k, self._data[n]
    
    def values(self) -> Iterable:
        for k,n in self._key_lookup.items():
            yield self._data[n]    
    
    def clear(self) -> None:
        """ D.clear() -> None.  Remove all items from D root with matching prefix
        
        Shall be avoided to use in a :class:`Prefixed` object
        """        
        pref = self._prefix+"."
        for k, n in list(self._key_lookup.items()):            
            self._data.pop(n)


def _setitem(d,k,v):
    d[k] = v
def _dummy_callback(data):
    pass
def _dummy_trigger():
    return True

class BaseDataLink:
    """ place holder for an instance check """    
    pass




@dataclass
class DownloadInput: 
    """ Collect information from one connection """
    nodes: set = field( default_factory=set) 
    datalinks: set = field( default_factory=set) 
    callbacks: List[Callback] = field( default_factory=list )
    failure_callbacks: List[Callback] = field( default_factory=list )

    def add_node(self, *nodes):
        self.nodes.update( nodes)
    def remove_node(self, *nodes):
        for node in nodes:
            try:
                self.nodes.remove(node)
            except KeyError:
                pass 
    
    def add_datalink( self, *datalinks):
        self.datalinks.update( datalinks)
    
    def remove_datalink(self, *datalinks):
        for dl in  datalinks:
            try:
                self.datalinks.remove(dl)
            except KeyError:
                pass 


    def add_callback(self, *callbacks, priority=0):
        for func in callbacks:
            self.callbacks.append( Callback(func, priority) )

    def remove_callback(self, *callbacks):
         for func in callbacks:
            for lc, p  in self.callbacks:
                if lc is func:
                    break 
            else:
                continue 
            try:
                self.callbacks.remove( Callback(func,p))
            except KeyError:
                pass 
       


    def add_failure_callback( self, *callbacks, priority=0):
         for func in callbacks:
            self.failure_callbacks.append( Callback(func, priority) )
    
    def remove_failure_callback(self, *callbacks):
        for func in callbacks:
            for lc, p  in self.failure_callbacks:
                if lc is func:
                    break 
            else:
                continue 
            try:
                self.failure_callbacks.remove( Callback(func,p))
            except KeyError:
                pass 

@dataclass
class DownloadInputs:
    connections: OrderedDict = field( default_factory= OrderedDict)
   
    def __getitem__(self, item):
        return self.connections[item]
    
    def has_token(self, token):
        return token in self.connections

    def iter_connection(self, tokens:Optional[List[Token]] = None):
        if tokens is None:
            tokens = self.connections
        for token in tokens:
            yield self.connections[token]

    def new_input(self, token: Token):
        self.connections[token] = DownloadInput() 
        return self.connections[token]
    
    def del_input(self, token: Token):
        del self.connections[token]

    def build_nodes(self, 
            tokens:Optional[List[Token]] = None,  
            data: Optional[Dict[BaseNode, Any]]=None
        )->Tuple[set, NodesReader]:
        
        nodes = set()
        for connection in self.iter_connection(tokens):
            nodes.update(connection.nodes)
            for dl in connection.datalinks:
                nodes.update(dl.rnodes)
               
        if data is not None:
            for n in nodes:
                data.setdefault( n, nodedefault(n, None) )

        return nodes
    
    def build_callbacks(self, tokens:Optional[List[Token]] = None )-> List[Callback]:
        callbacks = []
        for connection in self.iter_connection(tokens):
            callbacks.extend(connection.callbacks)
        callbacks.sort( key=lambda c:c.priority )
        return  [c.func for c in callbacks]

    def build_failure_callbacks(self, tokens:Optional[List[Token]] = None )-> List[Callback]:
        callbacks = []
        for connection in self.iter_connection(tokens):
            callbacks.extend(connection.failure_callbacks)
        callbacks.sort( key=lambda c:c.priority )
        return  [c.func for c in callbacks]
    
    def build_datalinks(self, tokens:Optional[List[Token]] = None )-> List[BaseDataLink]:
        datalinks = []
        for connection in self.iter_connection(tokens):
            datalinks.extend(connection.datalinks)
        return datalinks
    
    def build_downloader(self, 
            tokens:Optional[List[Token]] = None, 
            data: Optional[Dict[BaseNode,Any]] = None
        )-> Tuple[List[BaseNode], Callable]:
        nodes  = self.build_nodes( tokens, data )
        reader =  NodesReader(nodes)
        datalinks = self.build_datalinks( tokens ) 
        callbacks = self.build_callbacks( tokens )
        failure_callbacks = self.build_failure_callbacks( tokens )
        n_nodes = len(nodes)
        def download(data, info: DownloadInfo):
            info.start_time = time.time()
            try:
                reader.read(data)
            except Exception as e:
                info.error = e 
                info.n_node = 0

                if failure_callbacks:
                    for func in failure_callbacks:                    
                        func(e)
                else:
                    raise e            
            else:
                # Populate the data links 
                for dl in datalinks:
                    dl._download_from(data)
            
                if info.error:
                    info.error = None
                    for func in failure_callbacks:                    
                        func(None)
                        
                for func in callbacks:
                    func()
            info.n_nodes = n_nodes 
            info.end_time = time.time()
        return nodes, download        





class _BaseDownloader:
    def add_node(self,  *nodes) -> None:
        """ Register node to be downloaded for an iddentified app
        
        Args:
            *nodes :  nodes to be added to the download queue, associated to the app
        """
        self._check_connection() 

        self.inputs[self._token].add_node(*nodes) 
        self._rebuild()

    def add_nodes(self, nodes: Union[dict,Iterable]) -> None:
        """ Register nodes to be downloaded for an iddentified app
        
        Args:
           nodes (Iterable, dict):  nodes to be added to the download queue, associated to the app
                   If a dictionary of node/value pairs, they are added to the downloader data.  
        """
        self._check_connection() 

        if isinstance(nodes, dict):
            for node,val in nodes.items():
                self._data[node] = val
        self.inputs[self._token].add_node(*nodes) 
        self._rebuild() 
    

    def remove_node(self,  *nodes) -> None:
        """ Remove node from the download queue
    
        if the node is not in the queueu nothing is done or raised
        
        Note that the node will stay inside the downloader data but will not be updated 
        
        Args:
            *nodes :  nodes to be removed 
        """ 
        self._check_connection() 

        self.inputs[self._token].remove_node(*nodes) 
        self._rebuild()  
   
    def add_datalink(self,  *datalinks) -> None:
        """ Register a new datalink
        
        Args:
            *datalinks :  :class:`DataLink` to be added to the download queue, associated to the token 
        """ 
        self._check_connection() 

        self.inputs[self._token].add_datalink(*datalinks) 
        self._rebuild()  
   
    def remove_datalink(self, *datalinks) -> None:
        """ Remove a datalink from a established connection
        
        If the datalink is not in the queueu nothing is done or raised
        
        Args:
            *datalinks :  :class:`DataLink` objects to be removed         
        """
        self._check_connection() 

        self.inputs[self._token].remove_datalink(*datalinks) 
        self._rebuild()  
        
    def add_callback(self, *callbacks, priority=0) -> None:   
        """ Register callbacks to be executed after each download 
        
        The callback must have the signature f(), no arguments.
        
        Args:
            *callbacks :  callbacks to be added to the queue of callbacks, associated to the app
            priority (optional, int): a priority number for the callback 
                    at a lowest priority number, the callback is called first  
                    at highest priority number, the callback is called at the end 
        """
        self._check_connection() 

        self.inputs[self._token].add_callback(*callbacks, priority=priority) 
        self._rebuild()  
    
    def remove_callback(self,  *callbacks) -> None:   
        """ Remove callbacks 
        
        If the callback  is not in the queueu nothing is done or raised
        
        Args:
            
            *callbacks :  callbacks to be removed 
        
        """
        self._check_connection() 

        self.inputs[self._token].remove_callback(*callbacks) 
        self._rebuild() 
    
    def add_failure_callback(self, *callbacks, priority=0) -> None:  
        """ Add one or several callbacks to be executed when a download failed 
        
        When ever occur a failure (Exception during download) ``f(e)`` is called with ``e`` the exception. 
        If a download is successfull after a failure ``f(None)`` is called one time only.
                
        Args:
            *callbacks: callbacks to be added to the queue of failure callbacks, associated to the app
            priority (optional, int): a priority number for the callback 
                    at a lowest priority number, the callback is called first  
                    at highest priority number, the callback is called at the end 
        """ 
        self._check_connection() 

        self.inputs[self._token].add_failure_callback(*callbacks, priority=priority) 
        self._rebuild()  
    
    def remove_failure_callback(self,  *callbacks) -> None:  
        """ remove  one or several failure callbacks 
        
        If the callback  is not in the queue nothing is done or raised
        
        Args:
            
            *callbacks :  callbacks to be removed         
        """
        self._check_connection() 
        self.inputs[self._token].remove_failure_callback(*callbacks) 
        self._rebuild()  
    
    def run(self, 
            period: float =1.0, 
            stop_signal: Callable =lambda : False, 
            sleepfunc: Callable =time.sleep
        ) -> None:
        """ run the download indefinitely or when stop_signal return True 
        
        Args:
            period (float, optional): period between downloads in second
            stop_signal (callable, optional): a function returning True to stop the loop or False to continue
            
        """
        try:
            while not stop_signal():
                s_time = time.time()
                self.download()
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
   


class DownloaderConnection(_BaseDownloader):
    """ Hold a connection to a :class:`Downloader` 
    
    Most likely created by :meth:`Downloader.new_connection` 
    
    The download method of a Downloader Connection will download only the nodes of 
    the connection and its child connection. However the nodes values retrieved will 
    be writen inside the root data dictionary of the Downloader 


    Args:
       downloader (:class:`Downloader`) :  parent Downloader instance
       token (Any): Connection token 
    """
    def __init__(self, 
          downloader: "Downloader", 
          token: tuple, 
        ):
        self._downloader: Downloader = downloader 
        self._token = token 
        self._child_connections = [] 
        
        self.inputs = downloader.inputs 
        self.info = DownloadInfo()

       
    def _check_connection(self):
        if not self.is_connected():
            raise RuntimeError("DownloaderConnection has been disconnected from its Downloader")

    def _collect_tokens(self, tokens:List[Token]) -> None:
        if self._token:
            tokens.append( self._token) 
        for child in self._child_connections:
            child._collect_tokens(tokens) 
    
    def __has__(self, node):
        return node in self._nodes
  
    def _rebuild(self):
        tokens = []
        self._collect_tokens( tokens )
        self._nodes, self._download_func = self.inputs.build_downloader( tokens, self.data )
        parent = self._get_parent()
        if parent:
            parent._rebuild()

    def _get_parent(self):
        return None

    @property
    def data(self) -> dict:
        """ downloader data """
        return self._downloader.data 
    
    @property
    def nodes(self)->Set[BaseNode]:
        return self._nodes

    def download(self):
        self._download_func(self.data,  self.info)
    
    def is_connected(self)-> bool:
        """ Return True if the connection is still established """
        if not self._token:
            return False 
        return self._downloader.inputs.has_token(self._token)
    
    def clear(self)-> bool:
        """ Remove child connections from the list if they have been disonnected """
        self._child_connections = [child for child in self._child_connections if child.is_connected()]
        

    def disconnect(self) -> None:
        """ disconnect connection from the downloader 
        
        All nodes related to this connection (and not used by other connection) are removed from the
        the downloader queue. 
        Also all callback associated with this connection will be removed from the downloader 
        
        Note that the disconnected nodes will stay inside the downloader data but will not be updated
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
        def download(data, flag):
            raise ValueError("Disconnected")
        self._nodes, self._download_func = [] , download 
        parent = self._get_parent()
        if parent:
            parent._rebuild()
    
    def new_connection(self) -> "DownloaderConnection":
        """ create a new child connection. When the master connection will be disconnect, alll child 
        connection will be disconnected. 
        """
        connection =  self._downloader.new_connection() 
        self._child_connections.append(connection)
        connection._get_parent = weakref.ref( self )

        self._rebuild()
        return connection

class StopDownloader(StopIteration):
    pass

class Downloader(_BaseDownloader):
    """ object dedicated to download nodes, feed data and run some callback 

    An application can request nodes to be downloaded and callback to be executed after each 
    success download or each failures. 
    
    Args:    
        nodes_or_datalink (iterable of node or :class:`DataLink`): 
            - An initial, always downloaded, list of nodes 
            - Or a :class:`DataLink` object
        data (dict, optional): A dictionary to store the data. If not given, one is created and
                               accessible through the .data attribute. 
                               This data is made of node/value pairs, the .get_data_view gives however
                               a dictionary like object with string/value pairs. 
                               Each time a new node is added to the downloader it will be added to 
                               the data as ``data[node] = default``. where default is the node defaul or None 
                               it will be replaced after the next download.  
                               
        callback (callable, optional): one single function with signature f(), if given always 
                                      called after successful download. 
    """
    
    
    Connection = DownloaderConnection
    StopDownloader = StopDownloader
    
    def __init__(self,  
            nodes_or_datalink: Union[Iterable, BaseDataLink] = None,  
            data: Optional[Dict] = None, 
            callback: Optional[Callable] = None,
        ) -> None:
        if data is None:
            data = {}
               
        self._data = data 
        
        
        self._token = Ellipsis
        self.inputs = DownloadInputs()
        main_input = self.inputs.new_input( self._token ) 
        self.info = DownloadInfo() 

        if nodes_or_datalink:
            if isinstance(nodes_or_datalink, BaseDataLink):
                main_input.add_datalink(nodes_or_datalink)
            elif hasattr(nodes_or_datalink, "__iter__"):

                if isinstance( nodes_or_datalink, dict):
                    nodes_or_datalink = nodes_or_datalink.values()
                for v in nodes_or_datalink:
                    if isinstance( v, BaseDataLink ):
                        main_input.add_datalink( v) 
                    else:
                        main_input.add_node( v) 
        if callback:
            main_input.add_callback( callback )
               
        self._rebuild()        
        self._next_token = 1
        
    def __has__(self, node):
        return node in self._nodes
    
    def _rebuild(self):
        self._nodes, self._download_func = self.inputs.build_downloader(data = self._data)

    @property
    def data(self):
        return self._data
    
    @property 
    def nodes(self):
        return self._nodes 
    
    def _check_connection(self):
        pass

    def new_token(self) -> tuple:
        """ add a new app connection token
        
        Return:
           A token, the token and type itself is not relevant, it is just a unique ID to be used in 
                    add_node, add_callback, add_failure_callback, and disconnect methods 
                    
        .. note::
        
            new_connection() method return object containing a pair of token and downloader and all
                methods necessary to add_nodes, add_callbacks, etc ... 
                
        
        """
        token = Token(id(self), self._next_token)
        self.inputs.new_input( token ) 
        self._next_token += 1
        return token
    
    def new_connection(self):
        """ Return a :class:`DownloaderConnection` object 
        
        The :class:`DownloaderConnection` object contain a token and the downloader in order to have 
        a standalone object to handle the add/remove of queue nodes and callbacks 
        """
        connection = DownloaderConnection(self, self.new_token())
        connection._get_parent = weakref.ref(self)
        return connection 

    
     
    
    def download(self) -> None:
        """ Execute a download 
        
        Each nodes on the queue are fetched and the .data dictionary is updated
        from new values.
        
        """
        self._download_func(self.data, self.info)

      
    def reset(self) -> None:
        """ All nodes of the downloader with a reset method will be reseted """
        reset(self._nodes)
            
    def get_data_view(self, prefix: str ='') -> DataView:
        """ Return a view of the data in a dictionary where keys are string keys extracted from nodes
        
        If prefix is given the return object will be limited to items with key
        matching the prefix.  
        
        Note: the data view reflect any change made on the rootdata except when new nodes 
        (mathing the prefix) are added. So all necessary nodes shall be added to the downloader 
        before requesting a DataView. 
        
        Args:
           prefix (str, optional): limit the data viewer to a given prefix. prefix can also be an object 
                                with the key attribute like a :class:`BaseDevice`, :class:`BaseNode` etc ...
        
        Example:
            
            ::
                
                > downloader = Downloader([mgr.motor1.substate, mgr.motor1.pos_actual, mgr.motor2.substate])
                > downloader.download()
                > m1_data = downloader.get_data_view(mgr.motor1.key) 
                > m1_data['pos_actual']
                3.9898
            
            ::
            
                > m1_data = downloader.get_data_view(mgr.motor1)
                # is equivalent to 
                > m1_data = DataView(downloader.data, mgr.motor1)
        """
        return DataView(self._data, prefix)        
    
    def clean_data(self) -> None:
        """ Remove to the .data dictionary all keys/value pairs corresponding to nodes not in the downloader queue
        
        Returns:
           n (int): The number of node/value pair removed 
        """
        d = self.data
        count = 0
        for n in list(d): # list(d) in order to avoid deletion on the iterator
            if n not in self._nodes:
                d.pop(n, None)
                count+=1
        return count


def reset(nodes: Iterable):
    """ Execute the reset() method of a list of nodes """
    for n in nodes:
        n.reset()

def download(nodes, data: Optional[Dict] = None) -> Union[list,None]:
    """ read node values from remote servers in one call per server    

    Args:
        nodes (iterable, BaseObject):
             Iterable of nodes, like [mgr.motor1.stat.pos_actual, mgr.motor2.stat.pos_actual]
                    
        data (dict, optional):
             This is mostlikely a dictionary, must define a __setitem__ method
             If given the function return None and update data in place. 
             If data is None the function return a list of values 
             
        
    Returns:
       None, or list : download(nodes) -> return list of values 
                       download(nodes, data) -> return None and update the input data dictionary
    
    Example:
    
    ::
        
        data = {n:n.get() for n in nodes}
    
    Is equivalent, but **much slower** than 
    
    :: 
        
        data = {}
        download(nodes)
        
    The latest is more efficient because only one call (per server) is done.
    
    data dictionary is optional, if not given values are returned in a list:
    
    ::
     
        pos, error = download([mgr.motor1.stat.pos_actual, mgr.motor1.stat.pos_error])
     
    
    """

    if data is None:
        data = {}
        nodes = tuple(nodes) # in case this is a generator  
        NodesReader(nodes).read(data)
        return [data[n] for n in nodes]
    else:
        NodesReader(nodes).read(data)
        return None


