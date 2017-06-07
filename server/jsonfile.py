""" Simple utility to read and write JSON """
import os
import json
from logger import L

def load_json(path):
    """ given a path, return a structure with the contained JSON """
    dirname = os.path.dirname(path)
    if not dirname:
        name = os.path.basename(path)
        thisdir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(thisdir, name + '.json')

    filep = None
    try:
        filep = open(path)
    except IOError:
        L.warning("Can't open " + path + " for reading")
        return False

    data = {}
    filestr = filep.read()
    try:
        data = json.loads(filestr)
    except ValueError:
        L.error("Error: packet not valid json:" + filestr)
        filep.close()
        return False

    filep.close()
    return data

def save_json(path, data):
    """ given a path, and structure, save as JSON string """
    jsonstr = ""

    try:
        jsonstr = json.dumps(data)
    except TypeError:
        L.error("Error: data supplied can't be converted to JSON")
        return False

    dirname = os.path.dirname(path)
    if not dirname:
        name = os.path.basename(path)
        thisdir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(thisdir, name + '.json')

    filep = None
    try:
        filep = open(path, "w")
    except IOError:
        L.error("Error: can't open " + path + " for writing")
        return False

    filep.write(jsonstr)
    filep.write("\n")
    filep.close()
    return True

if __name__ == "__main__":

    def main():
        """ minimal test """
        data = load_json("config")
        if data is False:
            data = {}
        if "x" not in data:
            data["x"] = 0
        data["x"] += 1
        save_json("config", data)

    main()



