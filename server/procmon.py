""" Process monitor: scans processes and sends status to database """
import time
import json

from subprocess import Popen, PIPE

from db import DB
from reqhandler import RH

class Procmon(object):
    """ Procmon encapsulates information collection of OS process """
    def __init__(self):
        RH.register_handler('memlog', self.handle_memlog_req)

    def free_mem(self):
        """ caclulate free memory """
        pass

    def handle_memlog_req(self, packet):
        """ process the requset we regitered to handle """
        print("=========" + json.dumps(packet))
        start = packet['start']
        end = packet['end']
        mappings = 'get_mappings' in packet
        info = DB.get_proc_info(start, end, mappings)
        reply = {"reply-to":"meminfo", "data":info}
        return reply

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
            pcode = DB.get_code(proc)
            proclist.append((now, pcode, mem))
        DB.add_proc_info(proclist)

if __name__ == "__main__":
    PRMON = Procmon()
    PRMON.monitor()
