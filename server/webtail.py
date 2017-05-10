""" Process monitor: scans processes and sends status to database """
import time
import json

from reqhandler import RH
from logger import L
import jsonfile

# pylint: disable=W0703

# Python watchdog package:
# https://pypi.python.org/pypi/watchdog
# installed via: pip install watchdog

# Python watchdog documentation:
# http://pythonhosted.org/watchdog/api.html#module-watchdog.events

class WebTail(object):
    """ WebTail handles log files to monitor """
    def __init__(self):
        # set of file paths for which monitoring has been requested by all users
        self.path_filter = {}
        # mapping between client webtail plugin requests and this plugin's methods
        self.webtail_funcs = {
            "get_settings" : self.get_settings,
            "update_settings" : self.update_settings
        }
        self.tailed_file_ptrs = {}
        self.listeners = {}
        data = jsonfile.load_json("webtail")
        if data is False:
            data = {}
        self.config = data
        RH.register_websock_handlers('webtail',
                                     self.new_client,
                                     self.new_message,
                                     self.close_client)

    def log_exeption(self, ex, msg):
        """ generic exception logging """
        L.error(type(ex).__name__)
        L.error(msg)

    def follow(self):
        """ invoked by a timer event. Follow all files in aggregated list
            and send log deltas to listening clients """
        for fullpath in self.path_filter:
            self.follow_file(fullpath)

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
                    mconf = self.config[user]["monitored_files"]
                    if fullpath in mconf and not mconf[fullpath]["muted"]:
                        # file is in user's set of files to monitor and is not
                        # marked as muted
                        try:
                            info['l'] = lines
                            out = json.dumps(info)
                        except Exception as ex:
                            self.log_exeption(ex, "for json.dumps, line="+line)
                            break
                        websock.write_message(out)

            except Exception as ex:
                self.log_exeption(ex, "Exception while reading lines from:" + fullpath)

        where = filep.tell()
        filep.seek(where)

    def unfollow_file(self, fullpath):
        """ remove file from list of tracked files """
        if fullpath not in self.path_filter:
            return
        if fullpath not in self.tailed_file_ptrs:
            L.error("can't unfollow " + fullpath + " as it is not followed.")
            return
        self.tailed_file_ptrs[fullpath].close()
        del self.tailed_file_ptrs[fullpath]

    def get_fp(self, fullpath):
        """ given a path name, return and existing or created file pointer """
        filep = None
        if fullpath in self.tailed_file_ptrs:
            return self.tailed_file_ptrs[fullpath]
        try:
            filep = open(fullpath)
        except Exception as ex:
            self.log_exeption(ex, "opening file " + fullpath)
            return filep

        filep.seek(0, 2)
        self.tailed_file_ptrs[fullpath] = filep
        return filep

    def update_files_to_monitor(self, user, newclient):
        """ read user file monitor prefs and update monitoring paths if required """
        if user not in self.config:
            self.config[user] = {}
        user_config = self.config[user]
        if "monitored_files" not in user_config:
            user_config["monitored_files"] = {}
        if "regexes" not in user_config:
            user_config["regexes"] = []
        user_watched_files = user_config["monitored_files"]
        # L.info("==============")
        # L.info(user_watched_files)
        resave_config = False
        for filepath in user_watched_files:
            if filepath in self.path_filter and newclient:
                L.info(filepath + ": file already being monitored by another client")
                self.path_filter[filepath] += 1 # increase reference count
                continue

            if not self.get_fp(filepath):
                L.error("Bad file path for:"+filepath)
                user_watched_files[filepath]['follow'] = 0
                resave_config = True
                continue

            # First subscription to monitor this file
            self.path_filter[filepath] = 1

        if resave_config:
            # Some bad file paths encountered and were marked. Resave users configurations
            # with the marked bad paths so that they can be displayed on the client side
            self.save_config()

    def save_config(self):
        """ make the current configuration persistent """
        jsonfile.save_json("webtail", self.config)

    def new_client(self, user, client):
        """ invoked whenever a new client joins the service webtail"""
        L.info("received new client")
        self.listeners[client] = {"user": user}
        # new user means possibly more directories and files to monitor
        self.update_files_to_monitor(user, True)
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
        info = self.listeners[client]
        user = info['user']
        user_watched_files = self.config[user]["monitored_files"]
        for filepath in user_watched_files:
            if user_watched_files[filepath]["follow"]:
                self.path_filter[filepath] -= 1
                if self.path_filter[filepath] == 0:
                    L.info("reference count 0 for file "+filepath)
                    self.tailed_file_ptrs[filepath].close()
                    del self.tailed_file_ptrs[filepath]
                    del self.path_filter[filepath]

        del self.listeners[client]
        L.info("webtail - client closed")

    #-------------------------
    def update_settings(self, user, packet):
        """ update the set of files monitored by user """
        if "files" not in packet:
            return {"status":"error", "msg":"no files given"}

        if "regexes" not in packet:
            return {"status":"error", "msg":"no regexes given"}

        self.config[user]["monitored_files"] = packet['files']
        # The following can modify self.config[user]["monitored_files"]
        # if bad directories are included in that dictionary
        self.update_files_to_monitor(user, False)

        self.config[user]["regexes"] = packet['regexes']

        self.save_config()

        return {
            "status":"ok",
            "monitored":self.config[user]["monitored_files"],
            "regexes":self.config[user]["regexes"]
        }

    def get_settings(self, user, packet):
        """ get the set of files user is currently monitoring """
        mfiles = self.config[user]["monitored_files"]
        regexs = self.config[user]["regexes"]
        reply = {"status":"ok", "files":mfiles, "regexes":regexs}
        return reply
