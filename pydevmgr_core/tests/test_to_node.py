from pydevmgr_core import * 
import time

N = 1000

@to_node_class
def Toto1(scale=1.0, mean=0.0):
    return [scale, mean]
        
class Toto2(BaseNode):
    class Config(BaseNode.Config):
        scale: float = 1.0
        mean: float = 0.0
    def fget(self):
        return [self.config.scale, self.config.mean]

t1 = Toto1('')
t2 = Toto2('')
        
tic = time.time()
for i in range(N):
    t1.get()
toc = time.time()

print("Node Decorator ", (toc-tic)*1e6/N)

tic = time.time()
for i in range(N):
    t2.get()
toc = time.time()

print("Node Class", (toc-tic)*1e6/N)


@record_class
@to_parser_class
def Linear1(x, a=1.0, b=0.0, type="Linear"):
    return a*x+b
    
class Linear2(BaseParser):
    class Config(BaseParser.Config):
        a: float = 1.0
        b: float = 0.0
    @staticmethod
    def parse(x, config):
        return config.a*x + config.b

l1 = get_parser_class("Linear")()
l2 = Linear2()

tic = time.time()
for i in range(N):
    l1(10)
toc = time.time()

print("Parser Decorator", (toc-tic)*1e6/N)

tic = time.time()
for i in range(N):
    l2(10)
toc = time.time()

print("Parser Class", (toc-tic)*1e6/N)
