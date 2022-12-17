from typing import Any, Callable, Dict, List, Optional, Type 
from pydevmgr_core import BaseObject
from pydevmgr_core_ui.connector import BaseConnector
from .feedback import BaseFeedback 


class Action:
    """ Helper to define an "action" to be taken 

    The action is defined by a function and a list of function which must return 
    argument for the action's function (typicaly will returned by an UI entry).   
    """
    def __init__(self, func, fargs: Optional[List[Callable]] = None, feedback: Optional[BaseFeedback]= None):
        if fargs is None:
            self.fargs = []
        else:
            self.fargs = [f if hasattr(f, "__call__") else (lambda x=f: x) for f in fargs]
        self.func = func 
        self.feedback = feedback
        
    def call(self):
        if self.feedback:
            try:
                self.func( *self._collect_arguments() )
            except Exception as err:
                self.feedback.error(err)
            else:
                self.feedback.clear("")
        else:
            self.func( *(f() for f in self.fargs))
    
    def _collect_arguments(self):
        # grab errors and raise the first one
        # each getter function can have effect on ui in case of error 
        args = []
        errors = []
        for f in self.fargs:
            try:
                args.append( f() )
            except Exception as er:
                errors.append(er)
        if errors:
            raise errors[0]
        return args 
        

class ActionIndex:
    """ A dictionary of Action  

    The call method is expecting an index representing the action to take. 
    Use for QComboBox for instance 
    """
    def __init__(self, 
            actions: Optional[Dict[int, Action]] = None, 
            after: Optional[Callable] =None
        ):
        self.actions: Dict[int, Action] =  {} if actions is None else dict(actions)

        self.after = after
    
    def call(self, index: int):
        try:
            caller = self.actions[index]
        except KeyError:
            return 
        else:
            caller.call()
        if self.after: self.after()
    
    def add_action(self, index:int, action: Action):
        self.actions[index] = action   


class ActionMap:
    """ A dictionary of Action  

    Action are mapped to the ComboBox by name  
    """
    def __init__(self, 
            actions: Optional[Dict[str, Action]]= None, 
            after: Optional[Callable]= None
        ):
        self.actions: Dict[str, Action] = {} if actions is None else dict(actions)
        self.after = after
    
    def call(self, item: str):
        try:
            caller = self.actions[item]
        except KeyError:
            return 
        else:
            caller.call()
        if self.after: self.after()
    
    def add_action(self, item: str, action: Action):
        self.actions[item] = action   



