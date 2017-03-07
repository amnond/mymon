import time
import Queue

from subprocess import Popen, PIPE
from threading import Thread

from db import DB

class Procmon:
    def __init__(self):
        self.thread = Thread(target = self.monitor)
        self.db = DB()
        self.q  = Queue.Queue()

    def run(self):
        self.thread.start()
        while True:
            proclist = self.q.get(True)
            self.db.add_proc_info( proclist )

    def monitor(self):
        while True:
            time.sleep(20)
            now      = int(time.time())
            scommand = 'ps aux'
            cols     = (5,10)
            command  = scommand.split()

            process = Popen(command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            out   = stdout.splitlines()
            total = len(out)
            proclist = []
            for i in range(1,total):
                line = out[i]
                sline = line.split()
                mem = int(sline[cols[0]].decode('utf-8'))
                proc = ' '.join([x.decode('utf-8') for x in sline[cols[1]:]])
                procinfo = (now, proc, mem)
                proclist.append(procinfo)
            self.q.put(proclist)



