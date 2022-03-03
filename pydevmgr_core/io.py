import yaml
import os

from pydantic import BaseModel
from typing import Tuple, Optional, List, Dict, Optional, Callable, Any
from ._yaml_loader import PydevmgrLoader
from ._pkg_resource import PkgResource 

class IOConfig(BaseModel):
    cfgpath : str = 'CFGPATH'
    yaml_ext : Optional[List[str]] = ('.yml', '.yaml')
    YamlLoader = PydevmgrLoader
    
ioconfig = IOConfig()
pkg_res = PkgResource('pydevmgr_core', 'resources')    



def load_config(file_name: str, ioconfig: IOConfig = ioconfig) -> Dict:
    """ Load a configuration file into a dictionary
    
    The file name is given, it should be inside one of the path defined by the $CFGPATH 
    environment variable (or the one defined inside ioconfig.cfgpath). 
    
    Alternatively the path can be an absolute '/' path 

    For now only yaml configuration files are supported 

    Args:
        file_name (str): config file name. Should be inside one of the path defined by the $CFGPATH 
        environment variable. Alternatively the file_name can be an abosolute path
        ioconfig (optional): a :class:`IOConfig`        

    Returns:
        cfg (dict): config dictionary
    """
    return read_config(find_config(file_name, ioconfig = ioconfig), ioconfig = ioconfig)

def read_config(file: str, ioconfig: IOConfig =ioconfig) -> Dict:    
    """ Read the given configuration (yaml) file 
    
    Args:
        file (str): real file path, shall be a yaml file. 
    """
    with open(file) as f:
        return yaml.load(f.read(), Loader=ioconfig.YamlLoader)

def load_yaml(input: str, ioconfig: IOConfig =ioconfig) -> Any:
    return yaml.load(input, Loader=ioconfig.YamlLoader)

def find_config(file_name, ioconfig: IOConfig =ioconfig):
    """ find a config file and return its absolute path 
    
    Args:
        file_name (str): config file name. Should be inside one of the path defined by the $CFGPATH 
        environment variable. Alternatively the file_name can be an abosolute path
        ioconfig (optional): a :class:`IOConfig`        
    """
    path_list = os.environ.get(ioconfig.cfgpath, '.').split(':')
    for directory in path_list[::-1]:
        path = os.path.join(directory, file_name)
        if os.path.exists(path):
            return  path
    raise ValueError('coud not find config file %r in any of %s'%(file_name, path_list))

# overwrite the PydevmgrLoader.find_config method 
PydevmgrLoader.find_config = staticmethod(find_config)

    
def explore_config(filter: Optional[Callable] =None, ioconfig: IOConfig = ioconfig):
    """ Iterator on all config files found inside directories of the $CFGPATH environment variable 
    
    The iterator returns 

    Args:
        filter (None, callable, optional): if given it will receive the content for each file
               to filter
        ioconfig (optional): a :class:`IOConfig`               
    """
        
    path_list = os.environ.get(ioconfig.cfgpath, '.').split(':')
    found = set()
    
    for root in path_list[::-1]:
        for r, d, files in os.walk(root):
            for file in files:
                body, ext = os.path.splitext(file)
                if ext in ioconfig.yaml_ext:
                    p = os.path.relpath( os.path.join(r,file), root )
                    if not p in found:
                        if filter:
                            if filter(read_config(os.path.join(r,file))):
                                yield  p, root
                        else:
                            yield  p, root                                    
                    found.add(p)



def append_cfgpath( path: str, ioconfig: IOConfig = ioconfig):
    """ Add a new path to the $CFGPATH environment variable 

    Args:
        path (str): new config file directory 
        ioconfig (optional): a :class:`IOConfig` 
    """
    envpath = os.environ.get(ioconfig.cfgpath, '').split(':')
    envpath.append(path)
    os.environ[ioconfig.cfgpath] = ":".join(envpath)



