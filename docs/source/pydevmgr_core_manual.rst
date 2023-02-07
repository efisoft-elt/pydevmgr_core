Manual
======

.. warning:: Documentation In progress

  
:mod:`pydevmgr_core` contains only Base Classes to build so called, devices,
interface, nodes, and communication protocol. It does not do much by itself. 

The idea is to build a base framework to handle communication with distributed
devices. 


Install
-------

.. code-block:: shell

   pip install pydevmgr_core  


The sources can be found here : https://github.com/efisoft-elt/pydevmgr_core 



Objects
-------

Objects can be created directly in python as usual of from Factory classes and some arguments 
to build the object properly. Each objects have however a default Factory which is named Config. 


The config class handle object parameters exposed to user.

The idea is to separate the engines and business logic to the user configuration 
which can comme from external payload as a yaml configuration file for instance.

The configuration are `PYDANTIC`_ objects which brings data validation for all 
configuration. pydevmgr object are based on the :mod:`systemy`

By default, a Config class declared inside any pydevmgr object will inerit from the master class 

.. code-block:: python
    
    from pydevmgr_core import BaseDevice
    from pydevmgr_core.np_nodes import Noise
    
    class MyDevice(BaseDevice):
        class Config: 
            temp: Noise.Config( mean=22, scale=0.3 )
            model: str = "PT100"


    my_device = MyDevice()
    my_device.temp.get()
    
The `temp` is part of my_device attribute (Because it is configured as a node),  the `model` str 
configuraiton parameter is also accessible from `my_device` and is readonly : 

.. code-block:: python

    assert my_device.model == "PT100"

One can however change any configuration parameters thanks to the :meth:`BaseObject.reconfigure` 

.. code-block:: python 

    my_device.reconfigure( model = "PT100") 

    


One can also build a config from a payload, with some caveat explained below: 

.. code-block:: python

    payload = {"model": "PT100", "temp": {"scale": 2.0} }
    config = MyDevice.Config( **payload)
    assert config.temp.scale == 2.0
    assert config.temp.mean == 0.0  # <- Not 22.0

Because the "temp" payload is not complete, the mean value get the default value of the `Noise.Config` class 
and not the mean defined in the temp instance of ``MyDevice`` class. To avoid this pydevmgr has a 
:class:`pydevmgr_core.Defaults` typing object. 

.. code-block:: python

    from pydevmgr_core import BaseDevice, Defaults
    from pydevmgr_core.np_nodes import Noise
    
    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config): 
            temp: Defaults[Noise.Config] = Noise.Config( mean=22, scale=0.3 )
            model: str = "PT100"

    payload = {"model": "PT100", "temp": {"scale": 2.0} }
    config = MyDevice.Config( **payload)
    assert config.temp.scale == 2.0
    assert config.temp.mean == 22.0  # <- Yes, 22.0 


If a node,  or any other child object, has no vocation to be configured by the user, it can be directly
inserted to the parent class thanks to its Factory class (here  Config is the Factory) 

.. code-block:: python

    from pydevmgr_core import BaseDevice
    from pydevmgr_core.np_nodes import Noise
    
    class MyDevice(BaseDevice):
        temp = Noise.Config( scale=0.3, mean=22.0)
    
        
    my_device = MyDevice()
    my_device.temp.get()
    # some value around 22 with 0.3 sigma 

    assert not hasattr( my_device.config, "temp")  # temp node is not part of config 


Below is an other exemple but using an Factory rather than the default Config. The Factory 
is switching between to kind of objects function to user input.  

::

    from pydevmgr_core import BaseFactory, BaseDevice, BaseNode
    from pydevmgr_core.np_nodes import Noise
    from pydevmgr_core.nodes import Static
    from typing import Optional 

    class MyNodeFactory(BaseFactory):
        scale: float = 1.0
        mean: float = 0.0
        value: Optional[float] = None
        
        def build(self, parent, name):
            if self.value is None:
                return Noise.Config(scale=self.scale, mean=self.mean).build(parent, name)
            else:
                return Static.Config(value=self.value).build(parent, name)

    class MyDevice(BaseDevice): 
        my_node = MyNodeFactory( value=-9.9 )
        my_random_node = MyNodeFactory(scale=10) 
        
    
Therefore a ``Config`` object can be also used inside class declaration: 

::

    class MyDevice(BaseDevice):
        temp = Noise.Config( scale=0.3, mean=22.0)


        
    
.. _PYDANTIC: https://pydantic-docs.helpmanual.io



Parser
++++++

Nodes are using parser by default. Since version 0.6 the parser engine is a separate package
see :mod:`valueparser`

e.g. 

.. code-block:: python 

    from valueparser import Clipped
    
    p = Clipped( min=0.0, max=1.0 )
    
    assert p.parse(0.5) == 0.5
    assert p.parse(3.4) == 1.0


Node 
++++

In pydevmgr a Node is an object dedicated to retrieve or write data. The data
can be located anywhere, in a distant server for instance or on a hardware via a
serial communication. For each type of applications the Node as to be
implemented according to server or hardware capability. `pydevmgr_core` offers
the :class:`pydevmgr_core.BaseNode` which cannot do much by itself but is the
base brick for Node implementation. See for instance the `pydevmgr_ua:UaNode` to
retrieve a node value from an OPC-UA server. 

Like other pydevmgr nodes have a config attribute (instance of its Config factory) and an ``engine`` atribute. 
The engine attribute is created at object creation function to what is configured and function to the parent object
engine. For instance for a node in an OPC-UA server attached to a Device will use the opc-ua client connection
information defined inside the parent device engine. 

Nodes have a `get()` to retrieve value and a `set()` method 

.. code-block:: python
    
    # get the value (where ever it is, e.g. an OPC-UA server)
    value = my_node.get()

    # get the value from a data dictionary. Where data must have the node as key
    # (plus others if this is a node alias)
    value = my_node.get(data) 


    # set a value somehwere 
    my_node.set(value)
    
    # also set value inside a dictionary  
    my_node.set(value, data)
        

Node are mostly used by a parent object like a :class:`pydevmgr_core.BaseDevice` or
:class:`pydevmgr_core.BaseInterface`. The `classmethod` :meth:`pydevmgr_core.BaseNode.new` is used to build the node
within the context of its parent. The ``new`` method must have a fixed signature and is used by the Config factory. 


For this documentation, let us build a simple dummy Node that read/write global variables. For a more complete
development tutorial see code of :mod:`pydevmgr_ua`

::

    from pydevmgr_core import BaseNode
    
    test0 = 0
    test1 = 1
    test2 = 2
    test3 = 3


    class GlNode(BaseNode):
        class Config:
            var: str
        
        def fget(self):
            return globals()[self.var]
        
        def fset(self, value):
            globals()[self.var] = value

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


Each Node as a key to identify them, which can be handy in some context and make
sens when the node is built from a ``Device`` or a ``Interface``. If not given a
unique key is build. 

::
    
    >>> n1 = GlNode(key="my_node", var="test1")
    >>> n1.key 
    'my_node'

Node Aliases 
++++++++++++

NodeAlias mimic a real client Node. 
    
The NodeAlias object does a little bit of computation to return a value with its ``get()`` method and 
thanks to required input nodes. It can also implement a ``set()`` method. 
 

NodeAlias is an abstraction layer, it does not do anything complex but allows uniformity among ways to retrieve node values. 

NodeAlias object can be easely created with the @nodealias() decorator

..note::

    :class:`pydevmgr_core.NodeAlias` can accept one or several input node from the unique ``nodes`` argument. 
    To remove any embiguity NodeAlias1 is iddentical but use only one node as input from the ``node`` argument.  



Example: 

.. code-block:: python
    
    from pydevmgr_core import NodeAlias
    from pydevmgr_core.nodes import Value # static value for demo
    class Rescale(NodeAlias):
        """ Rescale a value """
        class Config:
            scale = 1.0
        def fget(self, value):
            return value * self.scale
     
    
    raw_node = Value( value=2.0 )
    scaled_node = Rescale( nodes=raw_node, scale=100.0)
    assert scaled_node.get() == 200.0

        

Of course it makes more sens when inserted inside a parent object: 

.. code-block:: python

    from pydevmgr_core import NodeAlias, BaseDevice
    from pydevmgr_core.nodes import Value # static value for demo
    
    class Rescale(NodeAlias):
        """ Rescale a value """
        class Config:
            scale = 1.0
        def fget(self, value):
            return value * self.scale
    
    class MyDevice(BaseDevice):
        class Config:
            rescaled = Rescale.Config( scale= 100.0, nodes="raw")
        raw = Value.Config( value=2.0 )
    
    device = MyDevice()
    assert device.rescaled.get() == 200.0
    device.raw.set(4.0)
    assert device.rescaled.get() == 400.0

On the example above the node is the string that lead to the input node from the parent object. 
Note that, on the exemple above the scaled node is configurable but not the raw node. 



Node alias can have several node at input

.. code-block:: python

    from pydevmgr_core import NodeAlias, BaseDevice
    from pydevmgr_core.nodes import Value # static value for demo
    from typing import Tuple
    class InTarget(NodeAlias):
        class Config:
            position: Tuple[float,float] = (0.0, 0.0)
            radius: float = 1.0
            pos_name: str = ""
        def fget(self, x, y):
            x0,y0 = self.position 
            return  ((x-x0)**2 + (y-y0)**2) <= self.radius**2
    
    
    class MyDevice(BaseDevice):
        class Config:
            is_in_position_a = InTarget.Config(nodes=["posx", "posy"], position=(2.3, 1.2), radius=0.4, pos_name="A")
        posx = Value.Config( value=2.22)
        posy = Value.Config( value=1.3)
            
    device = MyDevice(  )
    assert device.is_in_position_a.get() 
    device.posy.set( 4.5)
    assert not device.is_in_position_a.get() 


A node alias can be quickly created with the :func:`pydevmgr_core.nodealias` decorator, following above exemple:

.. code-block:: python

    from pydevmgr_core import nodealias, BaseDevice
    from pydevmgr_core.nodes import Value 
    from typing import Tuple


    class MyDevice(BaseDevice):
        class Config:
            pos_a: Tuple[float, float] = (0.0, 0.0)
            radius = 1.0  
        posx = Value.Config( value=2.22)
        posy = Value.Config( value=1.3)
        
        @nodealias("posx", "posy")
        def is_in_position_a(self, x, y):
            x0, y0 = self.pos_a
            return ((x-x0)**2 + (y-y0)**2) <= self.radius**2
    
    device = MyDevice( pos_a=(2.3, 1.2), radius=0.2)
    assert device.is_in_position_a.get() 
    device.posy.set( 4.5)
    assert not device.is_in_position_a.get() 


:func:`nodealias` accept an argument list of node input name  or instantiated nodes. 


If the input nodes are not know in advance one should instantiate the :class:`pydevmgr_core.BaseNodeAlias` instead and 
define the :meth:`pydevmgr_core.BaseNodeAlias.nodes`:

.. code-block:: python
    
    from pydevmgr_core import ParentWeakRef, BaseNodeAlias, BaseDevice
    from pydevmgr_core.nodes import Value 
    
    class Switcher(ParentWeakRef, BaseNodeAlias):
        def nodes(self):
            parent = self.get_parent()
            yield getattr(parent, parent.use)
        def fget(self, value):
            return value

    class MyDevice(BaseDevice):
        class Config:
            use = "value_a"
        value_a = Value.Config( value="a")
        value_b = Value.Config( value="b")
        value = Switcher.Config()

    device = MyDevice()
    assert device.value.get() == "a"
    device.reconfigure( use="value_b") 
    assert device.value.get() == "b"


On The exemple above the :class:`ParentWeakRef` is just implementing the get_parent() method and is subclassing the
new() method 


Rpc
+++

Interface
+++++++++

Device 
++++++

Manager 
+++++++



Functions & Tools
-----------------


Download & Upload
++++++++++++++++++

::

    from pydevmgr_core import upload, download

As mentioned above node values can be red from the ``.get`` method. However for
a large number of nodes retrieving node values one by one on a remote server can
be inefficient  because each node's get would be a request. The
:func:`pydevmgr_core.download` and :func:`pydevmgr_core.upload` are dedicated
for this purpose they can read and write a bunch of nodes in one call per server.

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




Module Indexes
==============

See also Alphabetical :ref:`genindex`


.. automodule:: pydevmgr_core
   :members: Parser, BaseNode, NodeAlias, BaseRpc, BaseInterface, BaseDevice, BaseManager, 
             download, Downloader, upload, Uploader
    

