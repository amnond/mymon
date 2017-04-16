import os
from os import path

directory_path = './static'
#files = [x for x in os.listdir(directory_path) if path.isfile(directory_path+os.sep+x)]
dirs = [x for x in os.listdir(directory_path) if path.isdir(directory_path+os.sep+x)]
print(dirs)