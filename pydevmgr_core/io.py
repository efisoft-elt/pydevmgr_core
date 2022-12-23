from pydevmgr_core.base.device import BaseDevice
from pydevmgr_core.base.manager import BaseManager
from .base.io import PydevmgrLoader, load_config, find_config, read_config, explore_config, append_cfgpath, ioconfig, parse_file_name
from pydevmgr_core.factories import DeviceFactory, ManagerFactory, ObjectFactory
from pydevmgr_core.base.base import kjoin 
from typing import Optional, Union 
from systemy import BaseFactory
import yaml

def open_object(
        cfgfile,
        key: Optional[str]= None, 
        path: Optional[Union[str, int]] = None, 
        prefix: str = '',
        Factory: BaseFactory = ObjectFactory
    ):
    """ open an object from a configuration file 
    Args:
        cfgfile: relative to on of the $CFPATH or absolute path to yaml config file 
        kind (optional, str): object kind as enumerated in KINDS ('Manager', 'Device', 'Interface', 'Node', 'Rpc')
            if None look inside the configuration file and raise error if not defined. 
        
        path (optional, str): an optional path to find the configuration inside the config file 
             'a.b.c' will go to cfg['a']['b']['c']
        default_type (optional, str): A default type if no type is defined in the configuration file
            If default_type is None and no type is found an error is raised

    Returns:
        obj : instanciatedpydevmgr object (Manager, Device, Node, Rpc, Interface)

    """
    
    _, p = parse_file_name(cfgfile)
    if p and path:
        raise ValueError("Path keyword given, but path is defined in filename")
    elif path:
        cfgfile = cfgfile + "(", path + ")"
    
    if key is None:
        _, p = parse_file_name(cfgfile)
        if p:
            key = p[-1]
            if prefix:
                key = kjoin( prefix, key)
    
    
    # factory = yaml.load( cfgfile, PydevmgrLoader)
    factory = load_config( cfgfile)
    if not isinstance(factory, BaseFactory):
        factory = Factory.parse_obj(factory) 
    return factory.build(None, key) 
    

def open_manager(cfgfile, path=None, prefix="", key=None, Factory=ManagerFactory):
    """ Open a manager from a configuration file 

        
        Args:
            cfgfile: relative path to one of the $CFGPATH or absolute path to the yaml config file 
            key: Key of the created Manager 
            path (str, int, optional): 'a.b.c' will loock to cfg['a']['b']['c'] in the file. If int it will loock to the Nth
                                        element in the file
            prefix (str, optional): additional prefix added to the name or key

        Output:
            manager (BaseManager subclass) :tanciated Manager class     
    """
    manager = open_object(
                cfgfile, 
                path=path, prefix=prefix, 
                key=key, Factory=Factory
            ) 
    if not isinstance(manager, BaseManager):
        raise ValueError("Not a Manager")
    return manager 


def open_device(cfgfile, path=None, prefix="", key=None, Factory=DeviceFactory):
    """ Open a device from a configuration file 

        
        Args:
            cfgfile: relative path to one of the $CFGPATH or absolute path to the yaml config file 
            key: Key of the created Device, if None one is taken from path 
            path (str, int, optional): 'a.b.c' will loock to cfg['a']['b']['c'] in the file. If int it will loock to the Nth
                                        element in the file
                                        
            prefix (str, optional): additional prefix added to the name or key

        Output:
            device (BaseDevice subclass) :tanciated Device class     
    """
    
    device =  open_object(cfgfile, path=path, prefix=prefix, key=key, Factory=Factory) 
    if not isinstance(device, BaseDevice):
        raise ValueError("Not a device")
    return device

