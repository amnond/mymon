"""
----------------------------------------------------------------
Daemonize code taken from: https://gist.github.com/slor/5946334

----------------------------------------------------------------

 An example of a Linux daemon written in Python.

Based on http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

The changes are:
1 - Uses file open context managers instead of calls to file().
2 - Forces stdin to /dev/null. stdout and stderr go to log files.
3 - Uses print instead of sys.stdout.write prior to pointing stdout to the log file.
4 - Omits try/excepts if they only wrap one error message w/ another.

http://stackoverflow.com/questions/3263672/python-the-difference-between-sys-stdout-write-and-print
"""
import atexit
import os
import signal
import sys
import time

from web import Web

LOGPATH = os.path.realpath(__file__)
OUTNAME = os.path.dirname(LOGPATH) + '/mymon_out.log'
ERRNAME = os.path.dirname(LOGPATH) + '/mymon_err.log'

def output(str):
    ''' temporary replacement for daemon output '''
    print(str)

class Daemon(object):
    """ Linux Daemon boilerplate. """
    def __init__(self, pid_file,
                 stdout=OUTNAME,
                 stderr=ERRNAME):
        self.stdout = stdout
        self.stderr = stderr
        self.pid_file = pid_file
        self.running = False

    def del_pid(self):
        """ Delete the pid file. """
        os.remove(self.pid_file)

    def daemonize(self):
        """ There shined a shiny daemon, In the middle, Of the road... """
        # fork 1 to spin off the child that will spawn the deamon.
        if os.fork():
            sys.exit()

        # This is the child.
        # 1. cd to root for a guarenteed working dir.
        # 2. clear the session id to clear the controlling TTY.
        # 3. set the umask so we have access to all files created by the daemon.
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # fork 2 ensures we can't get a controlling ttd.
        if os.fork():
            sys.exit()

        # This is a child that can't ever have a controlling TTY.
        # Now we shut down stdin and point stdout/stderr at log files.

        # stdin
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())

        # stderr - do this before stdout so that errors about setting stdout write to the log file.
        #
        # Exceptions raised after this point will be written to the log file.
        sys.stderr.flush()
        with open(self.stderr, 'a+', 0) as stderr:
            os.dup2(stderr.fileno(), sys.stderr.fileno())

        # stdout
        #
        # Print statements after this step will not work. Use sys.stdout
        # instead.
        sys.stdout.flush()
        with open(self.stdout, 'a+', 0) as stdout:
            os.dup2(stdout.fileno(), sys.stdout.fileno())

        # Write pid file
        # Before file creation, make sure we'll delete the pid file on exit!
        atexit.register(self.del_pid)
        pid = str(os.getpid())
        with open(self.pid_file, 'w+') as pid_file:
            pid_file.write('{0}'.format(pid))

    def get_pid_by_file(self):
        """ Return the pid read from the pid file. """
        try:
            with open(self.pid_file, 'r') as pid_file:
                pid = int(pid_file.read().strip())
            return pid
        except IOError:
            return

    def start(self):
        """ Start the daemon. """
        output("Starting...")
        if self.get_pid_by_file():
            output('PID file {0} exists. Is the deamon already running?'.format(self.pid_file))
            sys.exit(1)

        self.daemonize()
        self.run()

    def stop(self):
        """ Stop the daemon. """
        output("Stopping...")
        pid = self.get_pid_by_file()
        if not pid:
            output("PID file {0} doesn't exist. Is the daemon not running?".format(self.pid_file))
            return

        # Time to kill.
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            if 'No such process' in err.strerror and os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            else:
                output(err)
                sys.exit(1)

    def restart(self):
        """ Restart the deamon. """
        self.stop()
        self.start()

    def run(self):
        """ The main loop of the daemon. """
        self.running = True
        web = Web()
        web.ioloop()        # runs in this thread


def main():
    """ Handle daemon requests """
    if len(sys.argv) < 2:
        output("Usage: {0} start|stop|restart".format(sys.argv[0]))
        sys.exit(2)

    daemon = Daemon('/tmp/daemon_example.pid')
    if sys.argv[1] == 'start':
        daemon.start()
    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'restart':
        daemon.restart()
    else:
        output("Unknown command '{0}'".format(sys.argv[1]))
        sys.exit(2)

if __name__ == '__main__':
    main()

