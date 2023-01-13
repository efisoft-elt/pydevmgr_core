import re
import ast
import operator as op
from typing import Any, Generic, Tuple, TypeVar

from pydantic.error_wrappers import ValidationError
from pydantic.fields import ModelField



_path_glv = {'open':None, '__name__':None, '__file__':None, 'globals':None, 'locals':None, 'eval':None, 'exec':None,
        'compile':None}


_forbiden = re.compile( '.*[()].*' )


PathType = TypeVar('PathType')

class PathVar(Generic[PathType]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def __modify_schema__(cls, field_schema):
        pass 
    
    @classmethod
    def validate(cls, v, field: ModelField):
        
        

        if field.sub_fields:
            if len(field.sub_fields)>1:
                raise ValidationError(['to many field PathVar accep only one'], cls)

            val_f = field.sub_fields[0]
            errors = []
        
            valid_value, error = val_f.validate(v, {}, loc='value')
            if error:
                errors.append(error)
            if errors:
                raise ValidationError(errors, cls)
        else:
            valid_value = v 
        if not valid_value:
            return DummyPath()
        return objpath(valid_value)
    
    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'



class BasePath:
    def resolve(self, parent):
        raise NotImplementedError("resolve")
    
    def split(self):
        raise NotImplementedError("split")

    def set_value(self, root, value):
        raise NotImplementedError("set_value")

def objpath( path) -> BasePath:
    if isinstance( path, BasePath):
        return path
    if isinstance( path, str):
        if not path or path == ".":
            return DummyPath()
        return ObjPath(path)
    if hasattr( path, "__iter__"):
        return TuplePath(path)
    raise ValueError("invalid path argument")


class DummyPath(BasePath):
    def resolve(self, parent):
        return parent 
    def split(self)->Tuple[BasePath, BasePath]:
        raise ValueError("Cannot split a DummyPath")
    def set_value(self)->None:
        raise AttributeError("Cannot set value for DummyPath")

class ObjPath(BasePath):
    def __init__(self, path:str):
        if _forbiden.match(path):
            raise ValueError("Invalid path")
        self._path = path.lstrip(".")
        self._prefix = "" if path.startswith("[") else "."
    
    def resolve(self, parent):
        if not self._path:  return parent
               
        return eval( "parent"+self._prefix+self._path, _path_glv , {'parent':parent} ) 
    
    def set_value(self, root, value):
        
        exec( "parent"+self._prefix+self._path+" = value",  _path_glv , {'parent':root, 'value':value})
        

    def split(self)->Tuple[BasePath, BasePath]:
        if self._path.startswith("["): # Cannot split path item ? 
            return DummyPath(), self 
        
        splitted = [p  for p in self._path.split(".") if p]
        if len (splitted)>1:
            return TuplePath(tuple(splitted[0:-1])), ObjPath(splitted[-1] )
        else:
            return DummyPath(), ObjPath( splitted[0] )  

class ItemPath(BasePath):
    def __init__(self, item):
        self._item = item 
    def resolve(self, root):
        return root[self._item]
    
    def split( self):
        return DummyPath(), self 

    def set_value(self, root, value):
        root[self._item] = value 

class TuplePath(BasePath):
    def __init__(self, path):
        self._path = tuple(path)
    
    def resolve(self, root:Any)->Any:
        obj = root 
        try:
            for p in self._path:
                obj = getattr( obj, p)
        except AttributeError:
            raise AttributeError(f"cannot resolve path {self._path!r} on {root!r}")
        return obj
    
    def set_value(self, root, value):
        pr, attr = self.split()
        root = pr.resolve(root)
        attr.set_value( root, value)

        

    def split(self) -> Tuple[BasePath, BasePath]:
        if len(self._path)>1:
            return TuplePath( self._path[0:-1]), AttrPath(self._path[-1])
        else:
            return DummyPath(), AttrPath(self._path[0])
        

class AttrPath(BasePath):
    def __init__(self, attr: str):
        self._attr = attr
    
    def resolve(self, parent):
        return getattr(parent, self._attr)
        
    def split(self)->Tuple[BasePath, BasePath]:
        return DummyPath(), self
    
    def set_value(self, root, value)->None:
        setattr( root, self._attr, value)
