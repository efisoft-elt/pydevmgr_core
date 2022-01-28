
from pydantic import create_model, Extra, BaseModel, validator
from typing import Dict, Any, Optional, Union, Callable, Iterable, List, Dict, Tuple
from pydevmgr_core._core_objects._core_parser import create_parser_class, BaseParser, _BuiltParser, Clipped

class AnyParserConfig(BaseModel):
    type: Union[List[Union[str, Callable]], str, Callable] = ""
    class Config:
        extra = Extra.allow
        
class BaseNodeConfig(BaseModel):
    """ Config for a Node """
    kind: str = "Node"
    type: str = ""
    #parser: Optional[Union[str, Callable, Iterable]] = None
    parser: Optional[Union[AnyParserConfig, List[Union[str, Callable]], str, Callable]] = None
    #parser_config: dict = {}
    description: str = ""
    unit: str = ""
    
    class Config:
        validate_assignment = True
        


def parser(parsers, config=None, **kwargs):
    if isinstance(parsers, (BaseParser, _BuiltParser)) and not config and not kwargs:
        return parsers
    
    if isinstance(parsers, AnyParserConfig):
        Parser = create_parser_class(parsers.type)
        kwargs = {**kwargs, **parsers.dict(exclude=set(["type"]))}
    elif isinstance(parsers, dict):
        type_ = parsers.get('type', None)
        if not type_ :
            raise ValueError('parser type cannot be None')
        Parser = create_parser_class(type_)
        kwargs = {**parsers, **kwargs}    
    else:    
        Parser = create_parser_class(parsers)
    return Parser(config=config, **kwargs)        


def test_main():   
    assert parser(BaseNodeConfig(parser=float).parser)('4') == 4.0
    assert parser(BaseNodeConfig(parser={'type':'Float'}).parser)('4')
    assert parser(BaseNodeConfig(parser={'type':['Float','Clipped'], 'max':10}).parser)('12') == 10.0
    assert parser(BaseNodeConfig(parser='Float').parser)('4') == 4.0    
    assert parser(BaseNodeConfig(parser=Clipped(max=10)).parser)(12.0) == 10.0
    
    c = BaseNodeConfig(parser=Clipped(max=10))
    p = parser(c.parser)
    c.parser = p.config
    c.__dict__['parser'] = p.config
    assert c.parser is p.config    
    c.parser.max = 12
    assert p(13) == 12.0


if __name__ == "__main__":
    test_main()
    
