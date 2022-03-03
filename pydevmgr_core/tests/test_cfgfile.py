from pydevmgr_core import * 
from pydevmgr_core import io 
import os

# add the pkg resource to the cfg path, it contains test_node.yml, test_device.yml 
io.append_cfgpath( io.pkg_res.directory)


nodes = {
    'test1':{'cfgfile':'test_node.yml'},
    'test2':{'cfgfile':'test_node.yml', 'value':0}, 
    'test3': 'test_node.yml',
}


def test_main():

     i = BaseInterface( node_map = nodes)

     assert i.test1.config.value == 9
     assert i.test2.config.value == 0
     assert i.test3.config.value == 9
    
     io.load_config('test_device.yml')

     d = open_object('test_device.yml')
     d = BaseDevice.from_cfgfile('test_device.yml')
     d.i1.n1.get() == 9
     d.i1.n2.get() == 0
     d.n3.get() == 9
  


if __name__ == "__main__":
     test_main()   
