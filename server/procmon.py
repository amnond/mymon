""" Process monitor: scans processes and sends status to database """
import time
import psutil # https://github.com/giampaolo/psutil


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
        #print("=========" + json.dumps(packet))
        start = packet['start']
        end = packet['end']
        mappings = 'get_mappings' in packet
        info = DB.get_proc_info(start, end, mappings)
        reply = {"reply-to":"meminfo", "data":info}
        return reply

    def collect_userprocs_info(self):
        ''' Get diagnostics for all processes we can access without root permissions '''
        procdata = {}
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
            except psutil.NoSuchProcess:
                pass
            else:
                pid = pinfo['pid']
                name = pinfo['name']

                try:
                    prc = psutil.Process(pid)
                    mem = prc.memory_info()
                    #print("%s %d" % (name, mem))
                    if not name in procdata:
                        procdata[name] = {'rss':0}
                    procdata[name]['rss'] += mem.rss
                except psutil.AccessDenied:
                    pass
                    #print("AccessDenied for process %d (%s" % (pid, name))
                except psutil.ZombieProcess:
                    pass
                    #print("Zombie process %d (%s" % (pid, name))
        return procdata

    def monitor(self):
        """ scans OS processes and sends to database """
        procdata = self.collect_userprocs_info()
        now = int(time.time())
        proclist = []
        for name in procdata:
            mem = procdata[name]['rss']
            pcode = DB.get_code(name)
            proclist.append((now, pcode, mem))
        DB.add_proc_info(proclist)

if __name__ == "__main__":
    PRMON = Procmon()
    PRMON.monitor()
