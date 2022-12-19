import re
import ast
import operator as op



_path_glv = {'open':None, '__name__':None, '__file__':None, 'globals':None, 'locals':None, 'eval':None, 'exec':None,
        'compile':None}


_forbiden = re.compile( '.*[()].*' )

class BasePath:
    def resolve(self, parent):
        raise NotImplementedError("resolve")

class ObjPath(BasePath):
    def __init__(self, path):
        if _forbiden.match(path):
            raise ValueError("Invalid path")
        self._path = path
    
    def resolve(self, parent):
        return eval( "parent."+self._path, _path_glv , {'parent':parent} ) 
    
class AttrPath(BasePath):
    def __init__(self, attr: str):
        self._attr = attr
    
    def resolve(self, parent):
        return getattr(parent, self._attr)
        


