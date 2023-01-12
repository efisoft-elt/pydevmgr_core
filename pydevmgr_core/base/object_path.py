import re
import ast
import operator as op



_path_glv = {'open':None, '__name__':None, '__file__':None, 'globals':None, 'locals':None, 'eval':None, 'exec':None,
        'compile':None}


_forbiden = re.compile( '.*[()].*' )


class BasePath:
    def resolve(self, parent):
        raise NotImplementedError("resolve")

def objpath( path) -> BasePath:
    if isinstance( path, str):
        return ObjPath(path)
    if hasattr( path, "__iter__"):
        return TuplePath(path)
    if isinstance( path, BasePath):
        return path
    raise ValueError("invalid path argument")

class ObjPath(BasePath):
    def __init__(self, path):
        if _forbiden.match(path):
            raise ValueError("Invalid path")
        self._path = path
    
    def resolve(self, parent):
        if self._path == ".":  return parent 
        return eval( "parent."+self._path, _path_glv , {'parent':parent} ) 

class TuplePath(BasePath):
    def __init__(self, path):
        self._path = tuple(path)
    def resolve(self, root):
        obj = root 
        try:
            for p in self._path:
                obj = getattr( obj, p)
        except AttributeError:
            raise AttributeError(f"cannot resolve path {self._path!r} on {root!r}")
        return obj
        
            

class AttrPath(BasePath):
    def __init__(self, attr: str):
        self._attr = attr
    
    def resolve(self, parent):
        return getattr(parent, self._attr)
        


