'''
Various configuration settings of mymon
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

