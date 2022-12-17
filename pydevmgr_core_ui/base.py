ui_loockup = {}
def record_ui(namespace, object_type, kind):
    """ recorder for a new ui class for an object type and ui kind 

    Args:
        namespace: str, define the ui namspace , e.g. 'qt'
        object_type: a valid pydevmgr BaseObject :class:`pydevmgr_core.BaseDevice`
        kind: str widget kind for the guiven object 
    
    """
    def record(cls):
        ui_loockup[(namespace, kind, object_type)] = cls
        return cls
    return record

def get_ui_class(namespace, object_type, kind, default=None):
    """ Return an UI class for the given object and kind 

     Args:
        namespace: str, define the ui namspace , e.g. 'qt'
        object_type: a valid pydevmgr BaseObject :class:`pydevmgr_core.BaseDevice`
        kind: str widget kind for the guiven object 
  
    """

    try:
        return ui_loockup[(namespace, kind, object_type)]
    except KeyError:
        if default is None:
            raise ValueError(f"Cannot find a ui handler for kind={kind} and device type={object_type}") 
        else:
            return default 

