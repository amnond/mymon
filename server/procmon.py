""" Process monitor: scans processes and sends status to database """
import time

from subprocess import Popen, PIPE

from db import DB

class Procmon(object):
    """ Procmon encapsulates information collection of OS process """
    def __init__(self):
        self.pdb = DB()

    def free_mem(self):
        """ caclulate free memory """
        pass

    def monitor(self):
        """ scans OS processes and sends to database """
        now = int(time.time())
        cols = (5, 10)
        command = 'ps aux'.split()

        process = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            print(stderr)

        out = stdout.splitlines()
        total = len(out)
        proclist = []
        for i in range(1, total):
            sline = out[i].split()
            mem = int(sline[cols[0]].decode('utf-8'))
            proc = ' '.join([x.decode('utf-8') for x in sline[cols[1]:]])
            pcode = self.pdb.get_code(proc)
            proclist.append((now, pcode, mem))
        self.pdb.add_proc_info(proclist)

if __name__ == "__main__":
    PRMON = Procmon()
    PRMON.monitor()
