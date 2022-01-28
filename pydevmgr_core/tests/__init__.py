from . import test_cfgfile
from . import test_datalink
from . import test_dev_parser
from . import test_device
from . import test_device_config
from . import test_extra_node
from . import test_manager
from . import test_parser

def test_main():
    test_cfgfile.test_main()
    test_datalink.test_main()
    test_dev_parser.test_main()
    test_device.test_main()
    test_device_config.test_main()
    test_extra_node.test_main()
    test_manager.test_main()
    test_parser.test_main()
    
if __name__ == "__main__":
    test_main()
