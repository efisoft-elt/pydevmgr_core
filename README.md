Python package to by used as substitute of a real device manager running in a ELT-Software environment when the full ELT-Software environment cannot be used. 



Sources are [here](https://gitlab.lam.fr/efisoft/pydevmgr) 

The Documentation is [here](http://www.efisoft.fr/documentation/efisoft/pydevmgr/pydevmgr.html) 

 

# Install

```bash
> pip install pydevmgr 
```

# Basic Usage

```python 
from pydevmgr_elt import Motor, wait
m1 = Motor('motor1', address="opc.tcp://192.168.1.11:4840", prefix="MAIN.motor1")
try:
    m1.connect()    
    wait(m1.move_abs(3.2,1.0))
finally:
    m1.disconnect()
```
