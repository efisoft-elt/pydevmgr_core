import pkg_resources
import os

class PkgResource:
    def __init__(self, pkg_name, resource_dir="resources"):
        self._pkg_name = pkg_name
        self._resource_dir = resource_dir

    @property
    def directory(self):
        return pkg_resources.resource_filename(
                self._pkg_name, 
                self._resource_dir
                )
    def exists(self, resource_name):
        rpath = os.path.join(self._resource_dir, resource_name) 
        return pkg_resources.resource_exists(self._pkg_name, rpath)
    
    def find_resource(self, resource_name):
        if not self.exists(resource_name):
            raise ValueError(f"package resource {resource_name} not found ")
        rpath = os.path.join(self._resource_dir, resource_name) 
        return pkg_resources.resource_filename(self._pkg_name, rpath)


if __name__ == "__main__":
    pkg = PkgResource("pydevmgr_core")
    print('PACKAGE DIRECTORY', pkg.directory)
    pkg.exists('test_node.yml')
    print('test_node file is their:', pkg.find_resource('test_node.yml'))        
