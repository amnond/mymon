#----------------------------------------------------------------------------------------
# This requires the use of tornado (which requires pip)
#
# To install pip:
# $ wget -P Downloads/ http://python-distribute.org/distribute_setup.py
# $ sudo python Downloads/distribute_setup.py
# $ sudo easy_install pip
#
# To install tornado
# $ sudo pip install tornado
#
# Acknowledgements:
# https://gist.github.com/maximebf/1303842
# http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
# above link is dead in 2017, use this instead:
# https://gist.github.com/slor/5946334

import sys, os, time, atexit
from signal import SIGTERM

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import sys
import os

class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """

#--------------------------------------------------------------------------------------------

PNAME = os.path.abspath(__file__)
CWD   = os.getcwd()

#--------------------------------------------------------------------------------------------
class webTail:
    def __init__(self):
        self.port = 8879

        phperr = "/usr/local/openresty/nginx/logs/php.error.log"
        phplog = "/tmp/phplogs/phplog.txt"
        ngxlog = "/usr/local/openresty/nginx/logs/error.log"

        if not os.path.isdir("/var/www/admin"):
            ngxlog = CWD + "/logs/error.log"
            phperr = CWD + "/logs/php.error.log"

        self.filenames = [phperr, phplog, ngxlog]
        self.tailed_files = []
        self.listeners = []

    #-----------------------------------------
    def run(self):

        for filename in self.filenames:
            try:
                fp = open(filename)
                self.tailed_files.append(fp)
                fp.seek(0, os.SEEK_END)  # os.SEEK_END introduced in Python 2.5
            except IOError:
                print "could not open %s" % (filename)

        self.checkTimer = tornado.ioloop.PeriodicCallback(self.check_files, 500)
        webdir = os.path.dirname(PNAME)
        htmlpath = webdir+'/'+'webtail.html'
        filestr = open(htmlpath, 'r').read()
        application = tornado.web.Application([
            (r'/logs', MainHandler, dict(filestr=filestr)),
            (r'/tail/', TailHandler, dict(webTail=self)),
            (r'/(.*)', tornado.web.StaticFileHandler, {'path': webdir }), #TODO: check security!
         ])
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(self.port)
        io_loop = tornado.ioloop.IOLoop.instance()
        try:
            io_loop.start()
        except SystemExit, KeyboardInterrupt:
            io_loop.stop()
            for fp in self.tailed_files:
                fp.close()

    #-----------------------------------------
    def check_files(self):
        for fp in self.tailed_files:
            # for each file pointer, display what has happened since
            # the last chack. When using multiple files this may not
            # show correct chronology - the correct way to do this would
            # be to use python-inotify (on Linux) instead of polling or
            # make use of timestamps within the log files.
            where = fp.tell()
            line = fp.readline()
            if not line:
                fp.seek(where)
            else:
                while line:
                    for element in self.listeners:
                        element.write_message(line)
                    line = fp.readline()
            where = fp.tell()
            fp.seek(where)

    #-----------------------------------------
    def onOpen(self, client):
        self.listeners.append(client)
        if len(self.listeners)==1:
            # we have listeners - move all file pointers to end of file
            for fp in self.tailed_files:
                fp.seek(0, os.SEEK_END)
            # and start polling for changes in the monitored files
            self.checkTimer.start()

    #-----------------------------------------
    def onClose(self, client):
        try:
            self.listeners.remove(client)
            if len(self.listeners)==0:
                self.checkTimer.stop()
        except:
            pass

#--------------------------------------------------------------------------------------------
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, filestr):
        host = self.request.host
        self.html = filestr.replace("__HOST__",host)

    def get(self):
        self.write(self.html)

class TailHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, webTail):
        self.webTail = webTail

    def open(self):
        self.webTail.onOpen(self)

    def on_message(self, message):
        pass

    def on_close(self):
        self.webTail.onClose(self)


#--------------------------------------------------------------------------------------------
class MyDaemon(Daemon):
        def run(self):
            wt = webTail()
            wt.run()

#--------------------------------------------------------------------------------------------

if __name__ == "__main__":
    daemon = MyDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

