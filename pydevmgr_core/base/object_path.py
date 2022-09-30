import re
import ast
import operator as op



_path_glv = {'open':None, '__nane__':None, '__file__':None, 'globals':None, 'locals':None, 'eval':None, 'exec':None,
        'compile':None}


_forbiden = re.compile( '.*[()].*' )


class ObjPath:
    def __init__(self, path):
        if _forbiden.match(path):
            raise ValueError("Invalid path")
        self._path = path
    
    def resolve(self, parent):
        return eval( "parent."+self._path, _path_glv , {'parent':parent} ) 
    



