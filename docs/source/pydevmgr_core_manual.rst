Manual
======

.. warning:: Documentation In progress



pydevmgr_core module is the core library for pydevmgr it contains two modules : 

- pydevmgr_core - pydevmgr_core_qt , base QT classes to build widget 

:mod:`pydevmgr_core` contains only Base Classes to build so called, devices,
interface, nodes, and communication protocol. It does not do much by itself. 

The idea is to build a base framework to handle communication with distributed
devices. for this, it uses for this several objects ans some key functions. Let
us start with the main objects definition and usage.

Objects
-------

Parser
++++++

The class  :class:`pydevmgr_core.BaseParser`: defines an callable object used to
parse data. This parser is for instance used in a node to make sure that a user
value is correct and is eventually changed to be acceptable by the client
communication. 

The :class:`pydevmgr_core.BaseParser`: base parser class has a configuration (a
`Pydantic`_  ``BaseModel`` as for all config objects in pydevmgr) to specify
some parsing parameters. Example on the :class:`pydevmgr_core.Clipped` parser :

::

    from pydevmgr_core import Clipped
    
    p = Clipped( min=0.0, max=1.0 )
    
    assert p(0.5) == 0.5
    assert p(3.4) == 1.0
 
::

    >>> p.config
    Config(kind='Parser', type='Clipped', min=0.0, max=1.0)


One can combine Parser together for a chain of parsing, the only restriction is
that their is only one name space for config parameter. So a two parameters with
the same name will enter in collision.

::
    
    from pydevmgr_core import Bounded, Formula, parser
    
    p = parser((Bounded, Formula, ToString), min=0, max=1.0, formula="x * 100", format="%.2f %%")


::

    >>> p(0.4)
    '40.00 %'
    
 
The above example will raise an ValueError if the input value is outside [0,1],
apply the formula and convert it to string with a given format.

``min`` and ``max`` parameters are for the ``Bounded`` parser, ``formula``
obviously for the ``Formula`` parser and ``format`` for the ``ToString`` parser.  

As almost everything in pydevmgr, the parser can be embedded in a configuration
file, following the above example : 

::
    
    from pydevmgr_core import Bounded, Formula, parser
    import yaml 

    cfg = """
    type: [Bounded, Formula, ToString]
    min: 0.0 
    max: 1.0 
    formula: x * 100
    format: "%.2f %%"
    """

    p = parser( yaml.load(cfg) )
   

::

    >>> p(0.4)
    '40.00 %' 

Normal function can also be used and combined inside a parser : 

::
    
    from pydevmgr_core import Rounded, parser
    p = parser( (float, Rounded), ndigits = 2 )

::
    
    >>> p("3.141592653589793")
    3.14


Node 
++++

In pydevmgr a Node is an object dedicated to retrieve or write data. The data
can be located anywhere, in a distant server for instance or on a hardware via a
serial communication. For each type of applications the Node as to be
implemented according to server or hardware capability. `pydevmgr_core` offers
the :class:`pydevmgr_core.BaseNode` which cannot do much by itself but is the
base brick for Node implementation. See for instance the `pydevmgr_ua:UaNode` to
retrieve a node value from an OPC-UA server. 

Each Node type has its own __init__ signature, however the get and set method are
garanty to have always the same signature: 

::
    
    # get the value where ever it is (e.g. an OPC-UA server)
    value = my_node.get()

    # get the value from a data dictionary. Where data must have the node as key
    # (plus others if this is a node alias)
    value = my_node.get(data) 


::

    # set a value somehwere 
    my_node.set(value)
    
    # also 
    my_node.set(value, data)
        

Node are mostly used by a parent object like a :class:`pydevmgr_core.BaseDevice` or
:class:`pydevmgr_core.BaseInterface`. The `classmethod` :meth:`pydevmgr_core.BaseNode.new` is used to build the node
within the context of its parent. In other word ne first time one is doing::

    my_device.my_node 

The::

    MyNode.new( name, my_device )   

Is called and the node instance cashed inside ``my_device``. 



For this documentation, let us build a simple dummy Node that read/write global variables. For a more complete
development tutorial see code of ``pydevmgr_ua`` or  :ref:`Tuto` 

::

    from pydevmgr_core import BaseNode
    
    test0 = 0
    test1 = 1
    test2 = 2
    test3 = 3


    class GlNode(BaseNode):
        class Config(BaseNode.Config):
            var: str
        
        def fget(self):
            return globals()[self.config.var]
        
        def fset(self, value):
            globals()[self.config.var] = value

The node is used as follow

::
    
    n1 = GlNode(var="test1")
    n2 = GlNode(var="test2")
    n3 = GlNode(var="test3")

The `get` method retrieve the value, the `set` method write the value (when it
is possible)

::
    
    >>> n1.get()
    1
    >>> n1.set(10)
    >>> n1.get()
    10 


Each Node as a key to identify then, which can be handy in some context and make
sens when the node is built from a ``Device`` or a ``Interface``. If not given a
unique key is build. 

::
    
    >>> n1 = GlNode(key="my_node", var="test1")
    >>> n1.key 
    'my_node'





Download & Upload
++++++++++++++++++

::

    from pydevmgr_core import upload, download

As mentioned above node values can be red from the ``.get`` method. However for
a large number of nodes retrieving node values one by one on a remote server can
be inefficient  because each node's get would be a request. The
:func:`pydevmgr_core.download` and :func:`pydevmgr_core.upload` are dedicated
for this purpose they can read and write a bunch of nodes in one call.

With one argument (list of nodes), download returns a list of retrieved values.

::

    >>> v1, v2, v3 = download((n1,n2,n3))
    >>> v1
    10

With two arguments (second is a dictionary) the result is written inside the
second argument as a key/value pair where the key is the node itself.

::

    >>> data = {}
    >>> download( (n1,n2,n3), data )
    >>> v1 = data[n1]
    >>> v1
    10


The nodes entered in download and upload can be located in different server with
different protocol. The functions takes care of grouping nodes per server type
(thanks to the node ``.sid`` attribute) and ask servers one by one. So the
physical distribution of node values can change, the ``download`` function will
manage to retrieve the same things for the user.   



Upload works the same way but is expecting  node/value pairs inside a dcitionary::

    
    >>> upload( {n1:11, n2:12, n3:13} )



A class :class:`pydevmgr_core.Downloader` 



.. warning:: 

   This Documentation is in progress 



.. _Pydantic:  https://pydantic-docs.helpmanual.io/


Module Indexes
==============

See also Alphabetical :ref:`genindex`


.. automodule:: pydevmgr_core
   :members: BaseParser, BaseNode, NodeAlias, BaseRpc, BaseInterface, BaseDevice, BaseManager, 
             download, Downloader, upload, Uploader
    

