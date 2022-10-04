Manual
======

.. warning:: Documentation In progress



pydevmgr_core module is the core library for pydevmgr it contains two modules : 

- pydevmgr_core - pydevmgr_core_qt , base QT classes to build widget 

:mod:`pydevmgr_core` contains only Base Classes to build so called, devices,
interface, nodes, and communication protocol. It does not do much by itself. 

The idea is to build a base framework to handle communication with distributed
devices. Let us start with the main objects definition and usage.

Objects
-------

In pydevmgr several objects use a Config class to handle object parameters. 
The user configuration parameters are not directly implemented into the object 
but inside a ``.config`` structure attribute. However the config parameters can 
be set directly into the init function of object class or by parsing a ``config`` 
argument to the init object.

The idea is to separate the engines and business logic to the user configuration 
which can comme from external payload as a yaml configuration file for instance.

The configuration are `PYDANTIC`_ objects which brings data validation for all 
configuration.

In pydevmgr all config parameters stays inside the config structure of Base objects
except for :class:`pydevmgr_core.BaseDevice.Config`,  :class:`pydevmgr_core.BaseInterface.Config`,
:class:`pydevmgr_core.BaseNode.Config`,  :class:`pydevmgr_core.BaseRpc.Config`.

For instance if a Node ``Config`` is included inside a Device ``Config``
it gives to the device class an attribute to build dynamically the node. 
For instance:

::
    
    from pydevmgr_core import BaseDevice
    from pydevmgr_core.np_nodes import Noise
    
    class MyDevice(BaseDevice):
        class Config(BaseDevice.Config): 
            temp: Noise.Config = Noise.Config( mean=22, scale=0.3 )
            model: str = "PT100"


    my_device = MyDevice()
    my_device.temp.get()
    
The `temp` is part of my_device attribute (Because it is configured as a node) but not the `model` str 
configuraiton parameter which stays in config: 

::

    assert my_device.config.model == "PT100"


One can also build a config from a payload, with some caveat explained below: 

::

    payload = {"model": "PT100", "temp": {"scale": 2.0} }
    config = MyDevice.Config( **payload)
    assert config.temp.scale == 2.0
    assert config.temp.mean == 0.0  # <- Not 22.0

Because the "temp" payload is not complete, the mean value get the default value of the `Noise.Config` class 
and not the mean defined in the temp instance of ``MyDevice`` class. To avoid this pydevmgr has a 
:class:`pydevmgr_core.Defaults` typing object. 

::

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
inserted to the parent class thanks also to the `.Config`  class:


::

    from pydevmgr_core import BaseDevice
    from pydevmgr_core.np_nodes import Noise
    
    class MyDevice(BaseDevice):
        temp = Noise.Config( scale=0.3, mean=22.0)
    
        
    my_device = MyDevice()
    my_device.temp.get()
    # some value around 22 with 0.3 sigma 

    assert not hasattr( my_device.config, "temp")  # temp node is not part of config 



Actually a ``Config`` class is a special  :class:`pydevmgr_core.BaseFactory` (in v>0.6) which is responsible from inputs
argument to build the object from a parent object. The Factory class in this case is also use to hold configuration for
the object. One can make any kind of factory 

::

    from pydevmgr_core import BaseFactory, BaseDevice, BaseNode
    from pydevmgr_core,np_nodes import Noise
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
                return Static(value=self.value).build(parent, name)

    class MyDevice(BaseDevice): 
        my_node = MyNodeFactory( value=-9.9 )

    
Therefore a ``Config`` object can be also used inside class declaration to build an object as `.prop` method does  : 

::

    class MyDevice(BaseDevice):
        temp = Noise.Config( scale=0.3, mean=22.0)


        
    
.. _PYDANTIC: https://pydantic-docs.helpmanual.io



Parser
++++++

The class  :class:`pydevmgr_core.BaseParser`: defines an callable object used to
parse data. This parser is for instance used in a node to make sure that a user
value is correct and is eventually changed to be acceptable by the client/server 
communication.  

The :class:`pydevmgr_core.BaseParser`: base parser class has a configuration (a
`Pydantic`_  ``BaseModel`` as for all config objects in pydevmgr) to specify
some parsing parameters. Example on the :class:`pydevmgr_core.parsers.Clipped` parser :

::

    from pydevmgr_core.parsers import Clipped
    
    p = Clipped( min=0.0, max=1.0 )
    
    assert p(0.5) == 0.5
    assert p(3.4) == 1.0
 
::

    >>> p.config
    Config(kind='Parser', type='Clipped', min=0.0, max=1.0)


One can combine Parser together for a chain of parsing, the only restriction is
that their is only one name space for config parameters. So two parameters with
the same name will enter in conflict.

::

    from pydevmgr_core import parser 
    from pydevmgr_core.parsers import Bounded, Formula
    
    p = parser((Bounded, Formula, ToString), min=0, max=1.0, formula="x * 100", format="%.2f %%")


::

    >>> p(0.4)
    '40.00 %'
    
 
The above example will raise an ValueError if the input value is outside [0,1],
apply the formula and then convert it to string with a given format.

``min`` and ``max`` parameters are for the ``Bounded`` parser, ``formula``
obviously for the ``Formula`` parser and ``format`` for the ``ToString`` parser.  

As almost everything in pydevmgr, the parser can be embedded in a configuration
file, following the above example : 

::
    
    from pydevmgr_core.parsers import Bounded, Formula, ToString, parser
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

    >>> p.parse(0.4)
    '40.00 %' 

Normal function can also be used and combined inside a parser : 

::
    
    from pydevmgr_core.parsers import Rounded, parser
    p = parser( (float, Rounded), ndigits = 2 )

::
    
    >>> p.parse("3.141592653589793")
    3.14


Also one can create a combined parser class easily using the create_parser_class method 


::

    from pydevmgr_core.parsers import Bounded, Rounded
    from pydevmgr_core import create_parser_class
    
    BoundedNumber = create_parser_class( (Bounded, Rounded) )
    BoundedNumber.Config()

    #  BoundedRoundedConfig(kind=<KINDS.PARSER: 'Parser'>, type='BoundedRounded', ndigits=0, min=-inf, max=inf)

    
    parse_motor_efficiency = BoundedNumber( ndigits=2, min=0, max=1.0)    
    
A parser class can also be created with new default config parameters:


::

    from pydevmgr_core.parsers import Bounded, Rounded
    from pydevmgr_core import create_parser_class
    
    class Efficiency( create_parser_class((Bounded, Rounded)), min=0.0, max=1.0):
        pass

    parse_motor_efficiency = Efficiency( ndigits= 3) 

To create a costom parser class one can inerit from :class:`pydevmgr_core.BaseParser` and implement 
the ``fparse`` method as a static or classmethod  

::

    from pydevmgr_core import BaseParser
    
    class Prefixed(BaseParser):
        class Config(BaseParser.Config): 
            prefix: str # mendatory 

        @staticmethod
        def fparse( value, config): 
            if value.startswith(config.prefix): 
                return value
            return config.prefix+value 

    
    p = Prefixed( prefix="[WARNING] ")
    p.parse( "Something went wrong") 
        



Node 
++++

In pydevmgr a Node is an object dedicated to retrieve or write data. The data
can be located anywhere, in a distant server for instance or on a hardware via a
serial communication. For each type of applications the Node as to be
implemented according to server or hardware capability. `pydevmgr_core` offers
the :class:`pydevmgr_core.BaseNode` which cannot do much by itself but is the
base brick for Node implementation. See for instance the `pydevmgr_ua:UaNode` to
retrieve a node value from an OPC-UA server. 

Each Node type has its own `__init__` signature, most likely one will want to add to the `__init__` a 
socket, a serial com, or any open communication object used to retrieve the value, somewhere. But the ``new``
method has a fix signature and is used to create nodes in the context of a parent object. 
(:class:`pydevmgr_core.BaseDevice`, :class:`pydevmgr_core.BaseInterface`, ...).

::
    
    # get the value (where ever it is, e.g. an OPC-UA server)
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
within the context of its parent. The ``new`` method must have a fixed signature. 
In other word when doing this for the first time ::

    my_device.my_node 

The::

    MyNode.new( name, my_device )   

Is called and the node instance is cashed inside ``my_device``. 



For this documentation, let us build a simple dummy Node that read/write global variables. For a more complete
development tutorial see code of ``pydevmgr_ua``

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

Node Aliases 
++++++++++++


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
   :members: BaseParser, BaseNode, NodeAlias, BaseRpc, BaseInterface, BaseDevice, BaseManager, 
             download, Downloader, upload, Uploader
    

