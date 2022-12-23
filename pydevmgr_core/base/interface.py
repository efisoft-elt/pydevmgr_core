from .engine import BaseEngine
from .base import ( BaseObject,  BaseData )
                         

from .node import BaseNode
from .rpc import BaseRpc
from .decorators import finaliser
from enum import Enum 
from typing import Optional
#  ___ _   _ _____ _____ ____  _____ _    ____ _____ 
# |_ _| \ | |_   _| ____|  _ \|  ___/ \  / ___| ____|
#  | ||  \| | | | |  _| | |_) | |_ / _ \| |   |  _|  
#  | || |\  | | | | |___|  _ <|  _/ ___ \ |___| |___ 
# |___|_| \_| |_| |_____|_| \_\_|/_/   \_\____|_____|
# 


class BaseInterfaceConfig(BaseObject.Config):
    """ Config for a Interface """
    ...

class BaseInterface(BaseObject):
    """ BaseInterface is holding a key, and is in charge of building nodes """    
    
    Config = BaseInterfaceConfig
    Data = BaseData
    Node = BaseNode
    Rpc = BaseRpc   
    

    @classmethod
    def prop(cls,  name: Optional[str] = None, config_path=None, frozen_parameters=None,  **kwargs):
        cls._prop_deprecation( 'Interface: prop() method is deprecated, use instead the pydevmgr_core.decorators.finaliser to decorate the object creation tunning', name, config_path, frozen_parameters)
        return finaliser( cls.Config(**kwargs) )  
