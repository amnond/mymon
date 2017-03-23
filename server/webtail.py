""" Process monitor: scans processes and sends status to database """
import time
import threading
import json
from os import path

from reqhandler import RH
from logger import L

# Python watchdog package:
# https://pypi.python.org/pypi/watchdog
# installed via: pip install watchdog

# Python watchdog documentation:
# http://pythonhosted.org/watchdog/api.html#module-watchdog.events
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WebTail(FileSystemEventHandler):
    """ WebTail handles log files to monitor """
    def __init__(self):
        self.path_filter = {
            "/Users/amnondavid/projects/mymon/hello.txt" : 1
        }
        self.tailed_files = {}
        self.listeners = {}
        RH.register_websock_handlers('webtail',
                                     self.new_client,
                                     self.new_message,
                                     self.close_client)
        event_handler = self
        self.lock = threading.Lock()

        self.observer = Observer()
        self.observer.schedule(event_handler, path='..', recursive=False)
        self.observer.schedule(event_handler, path='.', recursive=False)
        self.observer.start() # start the watchdog thread
        self.event_methods = {
            "FileModifiedEvent" : self.on_file_modified,
            "FileCreatedEvent" : self.on_file_created,
            "FileDeletedEvent" : self.on_file_deleted,
            "FileMovedEvent" : self.on_file_moved
        }

    def on_any_event(self, event):
        normpath = path.normpath(event.src_path)
        fullpath = path.realpath(normpath)
        evtname = type(event).__name__
        if evtname not in self.event_methods:
            return
        #print "%s: %s" % ( evtname, fullpath )
        self.event_methods[evtname](fullpath)

    def follow_file(self, fullpath):
        """ get latest changes in a file and send to client """
        if fullpath not in self.path_filter:
            return
        filep = self.get_fp(fullpath)
        where = filep.tell()
        line = filep.readline()
        if not line:
            filep.seek(where)
        else:
            self.lock.acquire()
            try:
                info = {
                    "stime" : time.strftime("%Y-%m-%d %H:%M"),
                    "path" : fullpath,
                }
                while line:
                    info['line'] = line
                    for websock in self.listeners:
                        try:
                            out = json.dumps(info)
                        except:
                            L.error("for json.dumps, line="+line)
                            break
                        websock.write_message(out)
                    line = filep.readline()
            except Exception:
                L.error("Exception while reading lines from:" + fullpath)
            self.lock.release()
        where = filep.tell()
        filep.seek(where)

    def unfollow_file(self, fullpath):
        """ remove file from list of tracked files """
        if fullpath not in self.path_filter:
            return
        if fullpath not in self.tailed_files:
            L.error("can't unfollow " + fullpath + " as it is not followed.")
            return
        self.tailed_files[fullpath].close()
        del self.tailed_files[fullpath]
        pass

    def get_fp(self, fullpath):
        """ given a path name, return and existing or created file pointer """
        if fullpath in self.tailed_files:
            return self.tailed_files[fullpath]
        filep = open(fullpath)
        self.tailed_files[fullpath] = filep
        return filep

    def on_file_modified(self, fullpath):
        """ a file in the requested paths has been modified """
        self.follow_file(fullpath)

    def on_file_created(self, fullpath):
        """ a file in the requested paths has been created """
        self.follow_file(fullpath)

    def on_file_deleted(self, fullpath):
        """ a file in the requested paths has been deleted """
        self.unfollow_file(fullpath)

    def on_file_moved(self, fullpath):
        """ a file in the requested paths has been moved """
        self.unfollow_file(fullpath)

    def shutdown(self):
        """ close the watchdog thread and clean up """
        self.observer.stop()
        self.observer.join()

    def new_client(self, client):
        """ invoked whenever a new client joins the service webtail"""
        L.info("received new client")
        self.lock.acquire()
        self.listeners[client] = {}
        self.lock.release()
        return True

    def new_message(self, client, message):
        """ invoked whenever a client sends a new message to service webtail"""
        L.info("received new message:"+message)
        #client.write_message("hello from server")

    def close_client(self, client):
        """ invoked whenever a new client joins the service webtail"""
        self.lock.acquire()
        del self.listeners[client]
        self.lock.release()
        L.info("webtail - client closed")
