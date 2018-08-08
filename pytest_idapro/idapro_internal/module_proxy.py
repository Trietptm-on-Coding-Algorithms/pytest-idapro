import os
import sys
import types


class ProxyModuleLoader(object):
    def __init__(self):
        super(ProxyModuleLoader, self).__init__()
        self.loading = set()

    @staticmethod
    def is_idamodule(fullname):
        if fullname in ('idaapi', 'idc', 'idautils'):
            return True
        return fullname.startswith("ida_")

    def find_module(self, fullname, path=None):
        if fullname in self.loading:
            return None
        if path and os.path.normpath(os.path.dirname(__file__)) in path:
            return None
        if not self.is_idamodule(fullname):
            return None

        return self

    def load_module(self, fullname):
        # for reload to function properly, must return existing instance if one
        # exists
        print("Loading module", fullname)
        if fullname in sys.modules:
            return sys.modules[fullname]

        # otherwise, we'll create a module mockup
        # lock itself from continuously claiming to find ida modules, so that
        # the call to __import__ will not reach here again causing an infinite
        # recursion
        self.loading.add(fullname)
        real_module = __import__(fullname, None, None, "*")
        self.loading.remove(fullname)

        module = sys.modules[fullname] = ProxyModule(fullname, real_module)
        return module


class ProxyModule(types.ModuleType):
    def __init__(self, fullname, module):
        super(ProxyModule, self).__init__(fullname)
        self.__module = module
        print(self.__module)

    def __getattr__(self, name):
        return getattr(self.__module, name)

    def __setattr__(self, name, value):
        # TODO: implement set attr proxy
        pass


def install():
    print("preloaded modules", sys.modules.keys())
    sys.meta_path.insert(0, ProxyModuleLoader())
