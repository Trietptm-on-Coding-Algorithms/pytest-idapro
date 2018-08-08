import os
import sys
import types
import inspect

_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

# override print to remove dependencies
# because stdout/err are replaced with IDA's, using it will cause an inifinite
# recursion :)
def safe_print(*args):
    _orig_stdout.write(str(args) + "\n")


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
        if fullname in sys.modules:
            #if not self.is_idamodule(fullname):
                return sys.modules[fullname]

        safe_print("Loading module", fullname)
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
        object.__setattr__(self, '_ProxyModule__module', module)
        safe_print("Proxy initiated with module {}".format(module))

    def __getattribute__(self, name):
        if name == "_ProxyModule__module":
            return object.__getattribute__(self, "_ProxyModule__module")

        safe_print("Getattr called", self.__module, name)
        return getattr(self.__module, name)

    def __setattr__(self, name, value):
        safe_print("SETattr called", self.__module, name)
        return setattr(self.__module, name, value)


def install():
    safe_print("preloaded modules", sys.modules.keys())
    sys.meta_path.insert(0, ProxyModuleLoader())

    return
    whitelisted_modules = {'sys', 'swig_runtime_data4', 'logging', '__main__', 'rematch.network'}
    safe_print("Replacing preloaded modules")
    c = f = s = 0
    loaded_modules = list(sys.modules.keys())
    for module_name in loaded_modules:
        if module_name in whitelisted_modules:
            c += 1
            continue

        module = sys.modules[module_name]
        if not isinstance(module, types.ModuleType):
            c += 1
            continue

        safe_print(module_name, module, type(module))
        try:
            reload(module)
            safe_print(module_name, module, type(module))
            s += 1
        except (ImportError, TypeError):
            f += 1
            safe_print("Failed reloading module: {}".format(module))
            raise
        safe_print("reloaded successfuly: {}, continued: {}, failed: {} / {} modules".format(s, c, f, len(loaded_modules)))
