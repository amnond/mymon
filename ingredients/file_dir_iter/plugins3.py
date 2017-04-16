import os
from os import path
import inspect
import loadmodule

import pluginclass  # A plugin should subclass this

# https://chriscoughlin.com/2012/04/writing-a-python-plugin-framework/

directory_path = './plugins'
dirs = [x for x in os.listdir(directory_path) if path.isdir(directory_path+os.sep+x)]
# print(dirs)

for dirname in dirs:
  subdir = path.join(directory_path, dirname)
  files = [x for x in os.listdir(subdir) if path.isfile(path.join(subdir, x)) and x.endswith(".py")]
  for filename in files:
    plugin_candidate = path.join(subdir, filename)
    plugin_module = loadmodule.load_module(plugin_candidate)
    plugin_classes = inspect.getmembers(plugin_module, inspect.isclass)
    for plugin_class in plugin_classes:
    	pcls = plugin_class[1]
    	if issubclass(pcls, pluginclass.pluginclass):
            cls = pcls()
            cls.method1()
            cls.method2()
