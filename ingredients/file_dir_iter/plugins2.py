import os
from os import path
import loadclass

directory_path = './plugins'
# files = [x for x in os.listdir(directory_path) if path.isfile(directory_path+os.sep+x)]
dirs = [x for x in os.listdir(directory_path) if path.isdir(directory_path+os.sep+x)]
# print(dirs)

for dir in dirs:
  plugin = path.join(directory_path, dir, "mp.py")
  cl = loadclass.load_class(plugin, dir)
  cl.func1()


  plugin2 = path.join(directory_path, dir, "mp.py")
  c2 = loadclass.load_class(plugin2, "classname")
  c2.func1()
