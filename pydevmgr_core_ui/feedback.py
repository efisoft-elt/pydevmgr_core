from typing import Any

class BaseFeedback:
    """ A feedback standalone object called when an error occured """
    def error(self,  err: Exception):
        raise NotImplementedError('error')
        
    def clear(self, msg):
        raise NotImplementedError('clear')

class BaseContainerFeedback:
    """ A feedback object called when an error occured 

    function receive a ui container (for instance a QT object) in order to write 
    feedback. 
    """
    def error(self, container: Any, err: Exception):
        raise NotImplementedError('error')
        
    def clear(self, container: Any, msg):
        raise NotImplementedError('clear')

