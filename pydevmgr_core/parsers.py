from .base.register import register 
# from .base.parser_engine import BaseParser, parser
from valueparser import BaseParser, parser
from systemy import register_factory 

from .misc.math_parser import ExpEval

from enum import Enum
import math
from typing import Any, Optional , Type
from pydantic import validator
from py_expression_eval import Parser as _ExpressionParser 
_math_parser = _ExpressionParser()
del _ExpressionParser

from valueparser import (
        Int, Float, Complex, Bool, Str, Tuple, Set, Listed, 
        Clipped, Bounded, Formated, Rounded, Modulo, Enumerated 
        )



__all__ = [
"BaseParser", 
"parser", 
"Int", "Float", "Complex", "Bool", "Str", "Tuple", "Set", "List", 
"Clipped", "Bounded", "Loockup", 
"Enumerated", "Rounded", "ToString", "Capitalized", "Lowered", 
"Uppered", "Stripped", "LStripped", "RStripped", "Formula", 
]

def register(cls):
    return register_factory(cls.__name__, cls) 


class _Empty_:
    pass

@register
class Loockup(BaseParser):
    class Config(BaseParser.Config):
        loockup : list = []
        loockup_default : Optional[Any] = _Empty_
    
    @staticmethod
    def __parse__(value, config):
        if value not in config.loockup:
            try:
                if config.loockup_default is not _Empty_:
                    return config.loockup_default
                else:
                    raise ValueError(f'must be one of {config.loockup} got {value}')
            except KeyError:            
                raise ValueError(f'must be one of {config.loockup} got {value}')
        return value    


@register
class DefaultFloat(BaseParser):
    """ parse a float to a float or a default (e.g. NaN) if not a float """
    class Config(BaseParser.Config):
        default: float = math.nan
    
    @staticmethod
    def __parse__(value, config):
        try:
            return float( value)
        except (TypeError, ValueError):
            return config.default

@register
class ToString(BaseParser):
    class Config(BaseParser.Config):
        format : str = "%s"
        
    @staticmethod    
    def __parse__(value, config):
        return config.format%(value,)

@register
class Capitalized(BaseParser):
    @staticmethod
    def __parse__(value, config):
        return value.capitalize()

# @register(type="Lower")
@register
class Lowered(BaseParser):
    @staticmethod
    def __parse__(value, config):
        return value.lower()

# @register(type="Upper")
@register
class Uppered(BaseParser):
    @staticmethod
    def __parse__(value, config):
        return value.upper()

@register
class Stripped(BaseParser):
    class Config(BaseParser.Config):
        strip: Optional[str] = None
    @staticmethod
    def __parse__(value, config):
        return value.strip(config.strip)

@register
class LStripped(BaseParser):
    class Config(BaseParser.Config):
        lstrip: Optional[str] = None
    @staticmethod
    def __parse__(value, config):
        return value.lstrip(config.lstrip)

@register
class RStripped(BaseParser):
    class Config(BaseParser.Config):
        rstrip: Optional[str] = None
    @staticmethod
    def __parse__(value, config):
        return value.rstrip(config.rstrip)

@register
class Formula(BaseParser):
    class Config(BaseParser.Config):
        formula: str = 'x'
        varname: str = 'x'
    
    @staticmethod
    def __parse__(value, config):
        # Cash the Eval expression inside the condig.__dict__
        
        # exp = config.__dict__.setdefault( "__:"+config.formula, ExpEval(config.formula ))
        exp = ExpEval(config.formula )
        return exp.eval( {config.varname:value} ) 


@register
class Math(BaseParser):
    """ Parse a mathematical expression (string) to a value 

    If value is numerical, it is returned as such.
    """
    class Config(BaseParser.Config):
        variables: dict = {'pi':math.pi}
    @staticmethod
    def __parse__(value, config):
        if isinstance( value, (float, int, bool, complex)):
            return value
        return _math_parser.parse( value).evaluate(config.variables)
    
