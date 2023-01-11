from .base import ( BaseObject,  BaseData )
from .node import BaseNode
from .rpc import BaseRpc
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

