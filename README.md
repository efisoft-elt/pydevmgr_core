
This python package is used as a core engine for any pydevmgr high level package. 

The documentation is on its way, but one may be interested to higher level package such as 
- (pydevmgr_ua)[]
- (pydevmgr_elt)[]


Python package to by used as substitute of a real device manager running in a ELT-Software environment when the full ELT-Software environment cannot be used. 



Sources are [here](https://github.com/efisoft-elt/pydevmgr_core)


# Install

```bash
> pip install pydevmgr_core 
```

# Basic Usage

pydevmgr_core is not indented to be used directly but used by other pydevmgr related package as a core engine. 

For usage here is an example using pydevmgr_ua to access an OPC-UA node : 

```python
from pydevmgr_ua import UaNode, UaCom

com = UaCom(address="opc.tcp://192.168.1.11:4840", prefix="MAIN")
pos = UaNode("pos_actual", com=com,  suffix="Motor1.stat.lrPosActual" )

try:
    com.connect()
    print( "posisiotn is", pos.get() )
finally:
    com.disconnect()

```

Or using the highest level dedicated for ELT devices  : 


```python 
from pydevmgr_elt import Motor, wait
m1 = Motor('motor1', address="opc.tcp://192.168.1.11:4840", prefix="MAIN.Motor1")
try:
    m1.connect()    
    wait(m1.move_abs(3.2,1.0), lag=0.1)
    print( "position is", m1.stat.pos_actual.get() )
finally:
    m1.disconnect()
```
