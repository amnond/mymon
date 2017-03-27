""" Process monitor: scans processes and sends status to database """
import time
import threading
import json
from os import path

from reqhandler import RH
from logger import L
import jsonfile

# pylint: disable=W0703

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
        # set of file paths for which monitoring has been requested by all users
        self.path_filter = {}
        # set of derived directories that are being followed by watchdog observer
        self.follow_dirs = {}
        # mapping between client webtail plugin requests and this plugin's methods
        self.webtail_funcs = {
            "get_monitored_files" : self.get_monitored_files,
            "monitor_files" : self.monitor_files
        }
        self.tailed_files = {}
        self.listeners = {}
        data = jsonfile.load_json("webtail")
        if data is False:
            data = {}
        self.config = data
        RH.register_websock_handlers('webtail',
                                     self.new_client,
                                     self.new_message,
                                     self.close_client)
        event_handler = self
        self.lock = threading.Lock()

        self.observer = Observer()
        for directory in self.follow_dirs:
            self.observer.schedule(event_handler, path=directory, recursive=False)

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

    def log_exeption(self, ex, str):
        """ generic exception logging """
        L.error(type(ex).__name__)
        L.error(str)

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
                    "t" : time.strftime("%Y-%m-%d %H:%M:%S"),
                    "p" : fullpath,
                }
                lines = ""
                while line:
                    lines += line
                    line = filep.readline()

                out = ""
                for websock in self.listeners:
                    user = self.listeners[websock]["user"]
                    if fullpath in self.config[user]["monitored_files"]:
                        # file is in user's set of files to monitor
                        try:
                            info['l'] = lines
                            out = json.dumps(info)
                        except Exception as ex:
                            self.log_exeption(ex, "for json.dumps, line="+line)
                            break
                        websock.write_message(out)

            except Exception as ex:
                self.log_exeption(ex, "Exception while reading lines from:" + fullpath)

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
        # TODO: If we want to show the previous few log lines to every new user then
        #       we'll need tp save a file pointer for every user. This eems too wasteful
        #       for the added functionality
        #filep.seek(-240, 2) # point to (hopefully) a few lines before end of the file
        #filep.readline() # skip any semi line we've landed on
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

    def update_files_to_monitor(self, user):
        """ read user file monitor prefs and update monitoring paths if required """
        if user not in self.config:
            self.config[user] = {
                "monitored_files":{}
            }
        for filepath in self.config[user]["monitored_files"]:
            dirf = path.dirname(filepath)
            if dirf in self.follow_dirs:
                L.info(dirf + ": directory already being monitoed")
                self.follow_dirs[dirf] += 1 # TODO: implement ref couting
            else:
                self.observer.schedule(self, path=dirf, recursive=False)
                self.follow_dirs[dirf] = 1

            if filepath in self.path_filter:
                L.info(filepath + ": file already being monitoed")
                self.path_filter[filepath] += 1 # TODO: implement ref couting
            else:
                self.path_filter[filepath] = 1

    def save_config(self):
        """ make the current configuration persistent """
        jsonfile.save_json("webtail", self.config)

    def new_client(self, user, client):
        """ invoked whenever a new client joins the service webtail"""
        L.info("received new client")
        self.lock.acquire()
        self.listeners[client] = {"user": user}
        self.lock.release()
        self.update_files_to_monitor(user)
        return True

    def new_message(self, user, client, message):
        """ invoked whenever a client sends a new message to service webtail"""
        L.info("received new message:"+message)
        if client not in self.listeners:
            L.error("received message from unregiatered client")
            return
        reply_str = self.process_message(user, message)
        client.write_message(reply_str)

    def process_message(self, user, msg):
        """ process a request from a client-side webtail component """
        reply_packet = {"status":""}
        packet = {}
        try:
            packet = json.loads(msg)
        except Exception as ex:
            self.log_exeption(ex, "loading client request " + msg)
            reply_packet["status"] = "error"
            reply_packet["msg"] = "invalid request"
        if reply_packet["status"] == "error":
            return json.dumps(reply_packet)
        if "request" not in packet:
            reply_packet["status"] = "error"
            reply_packet["msg"] = "invalid request"
            L.error("webtail: no request in packet")
            return json.dumps(reply_packet)
        req = packet["request"]
        if req not in self.webtail_funcs:
            L.error("webtail: no handler for request")
            reply_packet["status"] = "error"
            reply_packet["msg"] = "invalid request"
            return json.dumps(reply_packet)
        reply_packet = self.webtail_funcs[req](user, packet)
        if "ctx" in packet:
            reply_packet["ctx"] = packet["ctx"]
        reply_packet["reply-to"] = req
        return json.dumps(reply_packet)


    def close_client(self, client):
        """ invoked whenever a new client joins the service webtail"""
        self.lock.acquire()
        del self.listeners[client]
        self.lock.release()
        L.info("webtail - client closed")

    #-------------------------
    def monitor_files(self, user, packet):
        """ update the set of files monitored by user """
        if "files" not in packet:
            return {"status":"error", "msg":"no files given"}

        mfiles = self.config[user]["monitored_files"]

        new = False
        for pathname in packet["files"]:
            if pathname not in mfiles:
                new = True
                mfiles[pathname] = 1

        if new:
            self.update_files_to_monitor(user)
            self.save_config()

        return {"status":"ok"}


    def get_monitored_files(self, user, packet):
        """ get the set of files user is currently monitoring """
        mfiles = self.config[user]["monitored_files"]
        reply = {"status":"ok", "files":mfiles}
        return reply
