'''
Varioud configuration settings of mymon - should be moved to JSON file
'''
import jsonfile

CONFIG = jsonfile.load_json("config")

OPT = {
    'DEBUG' : True,
    "plugins_order" : {}
}

if CONFIG:
    for key in CONFIG:
        OPT[key] = CONFIG[key]

