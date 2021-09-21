__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import os
import sys

if sys.version_info.major == 3:
    from importlib.util import spec_from_file_location
import imp

PUBLIC_MODULES = ["utils"]
PRIVATE_DIR = "_impl"


class PrivateMetaFinder(object):
    def find_spec(self, _fullname, path, target=None):
        if path is None or path == "":
            path = [os.getcwd()]  # top level import --
        if "." in _fullname:
            name = _fullname.split(".")[-1]
        else:
            name = _fullname

        glue = ""
        if name in PUBLIC_MODULES:
            glue = PRIVATE_DIR

        for entry in path:
            if glue:
                entry = os.path.join(entry, glue)

            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, "__init__.py")
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + ".py")
                submodule_locations = None
            if not os.path.exists(filename):
                continue
            if sys.version_info.major == 3:
                return spec_from_file_location(
                    _fullname,
                    filename,
                    loader=PrivateLoader(name, entry, filename),
                    submodule_search_locations=submodule_locations,
                )
            else:
                return PrivateLoader(name, entry, filename)
        return None  # we don't know how to import this

    # python 2:
    find_module = find_spec


class PrivateLoader(object):
    def __init__(self, name, path, filename):
        self.name = name
        self.filename = filename
        self.path = path

    def get_filename(self, fullname):
        return self.path

    # python 2:
    def load_module(self, _name):
        name = _name
        if "." in _name:
            name = _name.split(".")[-1]
        if _name in sys.modules:
            return sys.modules[_name]
        else:
            module_info = imp.find_module(name, [self.path])
            module = imp.load_module(_name, *module_info)
            sys.modules[_name] = module
        return module

    def get_data(self, filename):
        """exec_module is already defined for us, we just have to provide a way
        of getting the source code of the module"""
        with open(filename) as f:
            data = f.read()
        return data

    @property
    def loader(self):
        return self


sys.meta_path.insert(0, PrivateMetaFinder())
