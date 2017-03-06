#!/usr/bin/python

# Python watchdog package:
# https://pypi.python.org/pypi/watchdog

# Python watchdog documentation:
# http://pythonhosted.org/watchdog/api.html#module-watchdog.events

# Tornado with SSL documentation:
# http://stackoverflow.com/questions/18307131/how-to-create-https-tornado-server

import time
from os import path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        normpath = path.normpath(event.src_path)
        fullpath = path.realpath(normpath)
        print "%s: %s" % ( type(event).__name__, fullpath )

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path='..', recursive=False)
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
