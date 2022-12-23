

from pydantic import BaseModel, ValidationError
from pydantic.fields import ModelField
from typing import Optional, TypeVar, Generic 


RecVar= TypeVar('RecVar')

def _isdefault(field):
    try:
        return issubclass(field.type_, Defaults)
    except Exception:
        return False
                

def _default_walk_unset(  default: BaseModel, new: BaseModel ):
    
    if not isinstance( new, BaseModel ):
        return 
    
    fields = default.__fields__
    
    for k, v in default:
        if k in fields and _isdefault(fields[k]):
            sub = getattr(new, k)
            _default_walk_unset(v, sub)
        else:
            if not k in new.__fields_set__:
                # add the value directly inside __dict__ 
                # This is necessary otherwhise it will not work recursively 
                # Can be a huge draw back but not sure how to fix it, adding in __fields_set__ break the recursibility
                new.__dict__[k] = v
                # new.__fields_set__.add(k)


def _default_walk_set(  default: BaseModel, new: BaseModel ):
    
    if not isinstance( new, BaseModel ):
        return 
    
    

    fields = default.__fields__
    
    for k, v in default:
        if k in fields and _isdefault(fields[k]):
            sub = getattr(new, k)
            _default_walk_set(v, sub)
        else:
            if not k in new.__fields_set__ or ("__default__"+k) in new.__fields_set__:
                # add the value directly inside __dict__
                new.__dict__[k] = v
                # If the field has been set by the walker the __default__`key` shall be also in __fields__set__
                # so we need to update it to keep it recursive. The draw back is keys starting with  "__default__" in __fields__set__
                # but should not be a problem as it is used mostly for excluding stuff rather than building list of
                # stuff 
                new.__fields_set__.add("__default__"+k)
                new.__fields_set__.add(k)



class Defaults(Generic[RecVar]):
    """ Make the value of a default submodel the default values of the incoming payload 
    """
    _walker = _default_walk_set
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        #field_schema.update()
        pass

    @classmethod
    def validate(cls, v, field: ModelField):
        if not field.sub_fields:
            # Generic parameters were not provided so we don't try to validate
            # them and just return the value as is
            return v
        if len(field.sub_fields)!=1:
            raise ValidationError(['to many field Defaults require and accept only one argument'], cls)
            
        
        val_f = field.sub_fields[0]
        errors = []
        
        valid_value, error = val_f.validate(v, {}, loc='value')
        

        if error:
            errors.append(error)
        if errors:
            raise ValidationError(errors, cls)
        if field.default is not None:
            cls._walker(field.default, valid_value) 
        # Validation passed without errors, return validated value
        return valid_value
    
    def __repr__(self):
        return f'{self.__class__.__name__}({super().__repr__()})'


class Defaults2(Defaults):
    _walker = _default_walk_unset



if __name__ == "__main__":
    from pydantic import BaseModel
    from pydevmgr_core import BaseDevice, register
    from typing import Dict 
    
    @register
    class Toto(BaseDevice):
        class Config(BaseDevice.Config):
            type = "Toto"
            voltage: float = 12.0
    
    class C(BaseModel):
        n1: int = 0
        n2: int = 0

    class B(BaseModel):
        x: float = 0.0
        y: float = 0.0
        c1: Defaults[C] = C(n1=1)
        c2: Defaults[C] = C(n1=2)
        c3: C = C(n1=3)

    RB = Defaults[B]
    class A(BaseModel):
        b1: Defaults[B] = B(y=9)
        b2: Defaults[B] = B(y=8, c1=C(n1=100))
        
        devices: Dict[str,BaseDevice.Config] = {}

    a =A(b1={'x':1.0, 'c1':{'n2':10},  'c2':{'n2':20}, 'c3':{'n2':30}},    b2={'c1':{}}, 
            devices={ 'toto':{}, 'toto2':Toto.Config()}
    
        )

    print(a)
    
    assert a.b1.x == 1.0
    assert a.b1.y == 9.0 
    assert a.b1.c1.n2 == 10
    assert a.b1.c1.n1 == 1
    assert a.b1.c2.n1 == 2
    assert a.b1.c3.n1 == 0 # c3 is not a Defaults 

    assert a.b2.c1.n1 == 100
    
    assert "y" in a.b1.dict(exclude_unset=True)
  
