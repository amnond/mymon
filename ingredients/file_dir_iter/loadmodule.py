import sys

def load_module(filepath):
    ver = sys.version_info[0:2]

    if ver < (3, 4):
        import imp
        import os

        class_inst = None
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, filepath)

        elif file_ext.lower() == '.pyc':
            py_mod = imp.load_compiled(mod_name, filepath)

        return py_mod
    else:
        import importlib.util
        import os
        name = os.path.splitext(filepath)[0]
        modname =  os.path.split(name)[1]
        spec = importlib.util.spec_from_file_location(name, filepath)
        py_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_mod)
        return py_mod
