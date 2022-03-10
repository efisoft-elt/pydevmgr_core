# 0.3.3 
- the prop method nows built Config from cls.parse_config. So no record_class is needed for intermediate interfaces
- wait is fixed. It now wait on input nodes only. Before it was waiting on all downloaded nodes which cause problem for
  aliases, e.g. when the alias needs an other node which can be zero

# 0.3.2

- 2022/03/09 S.G behavior of default key is change in open_object when path is an integer 

# 0.3.1
- 2022/03/04   S.G    The InsideCircleNode is added to __all__ of toolbox
- 2022/03/04   S.G    MANIFEST.in file added to work with sdist 

