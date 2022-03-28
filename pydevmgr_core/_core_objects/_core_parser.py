from typing import Any, Optional, Type, Callable, Union, Iterable, List
from pydantic import BaseModel , create_model, Extra, validator
from inspect import signature , _ParameterKind, _empty, isbuiltin
from ._class_recorder import get_parser_class, KINDS, record_class
from ._core_base import reconfig
from .._misc.math_parser import ExpEval
import math
from enum import Enum 

parser_loockup = {}

class _Empty_:
    pass


class AnyParserConfig(BaseModel):
    """ A base model for any kind of parser """
    type: Union[List[Union[str, Callable]], str, Callable] = ""
    class Config:
        extra = Extra.allow

# Config for online built parser
class ParserConfig(BaseModel):
    kind: KINDS = KINDS.PARSER.value
    type: str = ""
    class Config:
        validate_assignment = True
        extra = "forbid"
        
# Config for parser classes 
class ParserElementConfig(BaseModel):    
    kind: KINDS = KINDS.PARSER.value
    type: str = ""
    class Config:
        validate_assignment = True
        extra = "forbid"
        
class BaseParser:       
    """ Callable Parser class """      
    Config = ParserElementConfig
    
    def __init_subclass__(cls, **kwargs) -> None:
        if kwargs:
            cls.Config = create_model(  cls.__name__+"Config",  __base__=cls.Config, **kwargs)
   
    def __init__(self, 
           config: Optional[ParserElementConfig] = None, 
           **kwargs
        ) -> None:
        self.config = reconfig(self.Config, config, kwargs)
    
    @staticmethod
    def parse(value, config: Optional[ParserElementConfig]) -> Any:
        return value 
    
    def __call__(self, value: Any) -> Any:        
        return self.parse(value, self.config)


class _BuiltParser:
    Config = ParserConfig
    __parsers__ = [] # yes this is the list and it is defined in the class 
    
    def __init__(self, config=None, **kwargs):
        self.config = reconfig(self.Config, config, kwargs)
    
    @classmethod
    def parse(cls, value, config):
        for parser in cls.__parsers__:
            value = parser(value, config)
        return value
    
    def __call__(self, value):
        return self.parse(value, self.config)        



def to_parser_class(_func_: Callable =None, *, type: Optional[str] = None) -> Type[BaseParser]:
    if _func_ is None:
        def parser_func_decorator(func):
            return _parser_func(func, type)
        return parser_func_decorator
    else:
        return _parser_func(_func_, type)


def _parser_func(func, type_):            
    if not hasattr(func, "__call__"):
        raise ValueError(f"{func} is not callable")
        
    try:    
        s = signature(func)
    except ValueError: # assume it is a builtin class with one argument 
        conf_args = {}
    else:
        posarg = False
        conf_args = {}
        for a,p in s.parameters.items():
            if not posarg: 
                if p.kind!=_ParameterKind.POSITIONAL_OR_KEYWORD:
                    if p.default != _empty:
                        raise ValueError("first function argument should not have default") 
                posarg = True
            else:
                if p.default == _empty:
                    raise ValueError("Only one positional argument accepted")
                if p.annotation == _empty:
                    conf_args[a] = p.default 
                else:
                    conf_args[a] = (p.annotation,p.default)
    
    extras = {}
    if type_ is None:        
        if  "type" in conf_args:
            type_  = conf_args['type']            
        else:
            type_ = func.__name__
            extras['type'] = type_
    else:
        extras['type'] = type_
        
    Config = create_model(type_+"Config", **extras, **conf_args, __base__=BaseParser.Config)
    
    
    if conf_args: 
        conf_args_set = set(conf_args)        
        def parser_func_method(arg, config):
            return func(arg, **{a:getattr(config,a) for a in conf_args_set})
    else:
        def parser_func_method(arg, config):
            return func(arg)
            
    return type(type_+"Parser", (BaseParser,), {'Config':Config, 'parse': staticmethod(parser_func_method)})
    

def func_parser_parse(func):
    def f_parse(value, config):
        return func(value)
    return f_parse



_dynamic_parser_class_loockup = {}
def create_parser_class(
       parsers : Union[Callable, Type[BaseParser], Type[_BuiltParser], BaseParser, str, Iterable]
    ) -> Type[_BuiltParser]:
    """ create a new parser class 
    
    From a list of parser class or instance create a new parser class. The parse function of the new
    class will execute each individual parse of the input classes. 
    The Config class of the new parser class is a combination of all Configs
    
    Args:
        parser: A list of type :class:`BaseParser` or :class:`_BuiltParser` or callable or str  
    
    Return:
        Cls (Type[_BuiltParser]): A new parser class 
        
    Example:
    
    ::
    
        >>> from pydevmgr_core import create_parser_class, Clipped, Rounded
        >>> FBR = create_parser_class( (float, Rounded, Clipped) )
        >>> FBR.Config()
        FloatRoundedClippedConfig(kind=<KINDS.PARSER: 'Parser'>, type='Rounded', min=-inf, max=inf, ndigits=0)
        >>> f = FBR( min=0.0, max=9.0, ndigits=2)
        >>> f(5.768976976)
        5.77
        >>> f(12.2323)
        9.0    
    
    ... seealso::
        - :func:`parser`
        - :class:`BaseParser`
        
    """
    
    if isinstance(parsers, str):        
        return get_parser_class(parsers)     
    elif isinstance(parsers, type) and issubclass(parsers, (BaseParser, _BuiltParser)): 
        return parsers
    
    try: # this can be the case if parsers is a type like float
        return get_parser_class(parsers) 
    except (ValueError, TypeError):
        pass
        
    if not hasattr(parsers, "__iter__") or isinstance(parsers, type):
        parsers = [parsers]
    
    # convert str to class before checking in loockup
    parsers = tuple(get_parser_class(p) if isinstance(p,str) else p for p in parsers)
    
    try:
        ParserClass = _dynamic_parser_class_loockup[parsers]
    except KeyError:
        pass
    else:
        return ParserClass
    
    
    _cls_parsers = []
    _model_bases = []
    _name = ""
    _type = ""
    
    
    for obj in parsers:  
        if isinstance(obj, (BaseParser, _BuiltParser)):
            ParserCls = obj.__class__
            _cls_parsers.append( ParserCls.parse )
            Tmp_model = create_model( ParserCls.Config.__name__, **obj.config.dict(exclude_unset=True), __base__= ParserCls.Config)
            _model_bases.append(Tmp_model)
            _name += ParserCls.__name__ + str(id(obj.config))
            _type += str(ParserCls.Config.__fields__['type'].default)
        elif isinstance(obj, type) and issubclass(obj, (BaseParser, _BuiltParser)): 
            ParserCls = obj 
            _cls_parsers.append( ParserCls.parse )                                      
            _model_bases.append(obj.Config)
            _name +=  ParserCls.__name__         
            _type += str(ParserCls.Config.__fields__['type'].default)
            
        elif hasattr(obj, "__call__"):
            _cls_parsers.append( func_parser_parse(obj) )
            _name += getattr(obj, "__name__", "F"+str(id(obj))).capitalize()
            _type += getattr(obj, "__name__", "F"+str(id(obj))).capitalize()
        else:
            raise ValueError(f"Expecting valid parser object got a {type(obj)}")  
                
    if _model_bases:                    
        Config = type(_name+"Config", tuple(_model_bases), {'type':_type})
        ParserClass = type(_name, (_BuiltParser,), {'Config':Config, '__parsers__':_cls_parsers})
    else:
        Config = type(_name+"Config", (ParserConfig,), {'type':_type})
        ParserClass = type(_name, (_BuiltParser,), {'__parsers__':_cls_parsers, 'Config':Config})
    _dynamic_parser_class_loockup[parsers] = ParserClass 
    if _type: 
        record_class(ParserClass, overwrite=True)
    return ParserClass

# def parser(parsers, config=None, **kwargs):
#     Parser = create_parser_class(parsers)
#     return Parser(config=config, **kwargs)        

def parser(parsers, config=None, **kwargs):
    """ return a :class:`BaseParser` object 
    
    Args:
       parsers: :class:`BaseParser` or :class:`_BuiltParser` or :class:`BaseParser.Config`
                or dict or string. 
                Definne the parser class used
       config: optional, configuration of the parser 
       \*\*kwargs:  Additional key/value configuration pairs 
       
    Exemple::
    
    ::
    
        >>> from pydevmgr_core import parser, Bounded, Rounded
        >>> p = parser( (float,Bounded,Rounded), min=0, max=1.0, ndigits=2)
        >>> p('0.223546243')
        0.22
        >>> p(5.0)
        ValueError: 5.0 is higher than 1.0
        
        Note:
        >>>  p = parser( (float,"Bounded","Rounded"), min=0, max=1.0, ndigits=2)
        # works as well as Bounded and Rounded are recorded classes
        
    ::
       
        >>> from pydevmgr_core import parser, Formula, Clipped
        >>> p = parser( (float, Formula, Clipped), formula="2*x+10", max=100)
        >>> [p(10), p(20), p(30), p(40), p(50), p(60)]
        [30.0, 50.0, 70.0, 90.0, 100.0, 100.0]
        
    ::
    
        
    .. seealso::
        :func:`create_parser_class`
        
    """ 
    if isinstance(parsers, (BaseParser, _BuiltParser)) and not config and not kwargs:
        return parsers
    
    if isinstance(parsers, AnyParserConfig): # Use for a generic config of parser
        Parser = create_parser_class(parsers.type)
        kwargs = {**kwargs, **parsers.dict(exclude=set(["type"]))}
        
    elif isinstance(parsers, (BaseParser.Config, _BuiltParser.Config)):
        return get_parser_class(parsers.type)(config=parsers, **kwargs)
        
    elif isinstance(parsers, dict):
        type_ = parsers.get('type', None)
        if not type_ :
            raise ValueError('parser type cannot be None')
        Parser = create_parser_class(type_)
        parsers = dict(parsers) # make a copy 
        parsers.pop("type", None) # type shall be inside the class definition (always as a string)
        kwargs = {**parsers, **kwargs}    
    else:    
        Parser = create_parser_class(parsers)
    return Parser(config=config, **kwargs)        




def _make_global_parsers():
    """ Build automaticaly some parser from python types """
    for tpe in [int, float, complex, bool, str, tuple, set, list]:        
        Tpe = tpe.__name__.capitalize()
        def parse(value, config, tpe=tpe):
            return tpe(value)
        class Config(BaseParser.Config):
            type: str = Tpe 
        cls = type( Tpe , (BaseParser,), {'parse':staticmethod(parse), 'Config':Config} )    
        record_class(cls)
        record_class(cls, type=tpe.__name__)
        globals()[ Tpe ] = cls
_make_global_parsers()

@record_class  
class Clipped(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Clipped"        
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def parse(value, config):
        return min(config.max,max(config.min, value))
            
@record_class
class Bounded(BaseParser):
    class Config(BaseParser.Config): 
        type: str = "Bounded" 
        min: float = -math.inf
        max: float = math.inf
    
    @staticmethod
    def parse(value, config):        
        if value<config.min :
            raise ValueError(f'{value} is lower than {config.min}')
        if value>config.max :
            raise ValueError(f'{value} is higher than {config.max}')
        return value

@record_class
class Loockup(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Loockup"     
        loockup : list = []
        loockup_default : Optional[Any] = _Empty_
    
    @staticmethod
    def parse(value, config):
        if value not in config.loockup:
            try:
                if config.loockup_default is not _Empty_:
                    return config.loockup_default
                else:
                    raise ValueError(f'must be one of {config.loockup} got {value}')
            except KeyError:            
                raise ValueError(f'must be one of {config.loockup} got {value}')
        return value    


class _BaseEnum(Enum):
    pass
    
@record_class
class Enumerated(BaseParser):    
    class Config(BaseParser.Config):
        type = "Enumerated"
        enumname: str = "" # name of the Enum class if enumarator is a dictionary 
        enumerator: Type = _BaseEnum 
        
        @validator("enumerator", pre=True, check_fields=False)
        def _enum_validator(cls, value, values):
            if isinstance( value, list):
                value = dict(value)
            if isinstance(value, dict):
                return Enum( values['enumname'] or "TmpEnumerator", value)
            return value 
            
    @staticmethod
    def parse(value, config):
        return config.enumerator(value)    
        
@record_class
class Rounded(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Rounded"      
        ndigits: Optional[int] = 0 
        
    @staticmethod      
    def parse(value, config):
        return round(value, config.ndigits)          

@record_class
class ToString(BaseParser):
    class Config(BaseParser.Config):
        type: str = "ToString"      
        format : str = "%s"
        
    @staticmethod    
    def parse(value, config):
        return config.format%(value,)

@record_class
class Capitalized(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Capitalized" 
    @staticmethod
    def parse(value, config):
        return value.capitalize()

@record_class(type="Lower")
@record_class
class Lowered(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Lowered"
    @staticmethod
    def parse(value, config):
        return value.lower()

@record_class(type="Upper")
@record_class
class Uppered(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Uppered"
    @staticmethod
    def parse(value, config):
        return value.upper()

@record_class
class Stripped(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Stripped"
        strip: Optional[str] = None
    @staticmethod
    def parse(value, config):
        return value.strip(config.strip)

@record_class
class LStripped(BaseParser):
    class Config(BaseParser.Config):
        type: str = "LStripped"
        lstrip: Optional[str] = None
    @staticmethod
    def parse(value, config):
        return value.lstrip(config.lstrip)

@record_class
class RStripped(BaseParser):
    class Config(BaseParser.Config):
        type: str = "RStripped"
        rstrip: Optional[str] = None
    @staticmethod
    def parse(value, config):
        return value.rstrip(config.rstrip)


@record_class
class Formula(BaseParser):
    class Config(BaseParser.Config):
        type: str = "Formula"
        formula: str = 'x'
        varname: str = 'x'
    
    @staticmethod
    def parse(value, config):
        # Cash the Eval expression inside the condig.__dict__
        exp = config.__dict__.setdefault( "__:"+config.formula, ExpEval(config.formula ))
        return exp.eval( {config.varname:value} ) 
        

        # return ExpEval(config.formula).eval({config.varname:value})            
        
