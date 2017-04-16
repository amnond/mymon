import sys

def load_class(filepath, expected_class):
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

        if hasattr(py_mod, expected_class):
            class_inst = getattr(py_mod, expected_class)()

        return class_inst
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(expected_class, filepath)
        py_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_mod)
        return getattr(py_mod, expected_class)()

def 
if __name__ == "__main__":
    L = load_class('./procmon.py', 'Procmon')
    L.monitor()
