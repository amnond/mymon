from mmplugin import MymonPlugin

from reqhandler import RH

import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
L = logging.getLogger('system')


from db import _DB

""" Process monitor: scans processes and sends status to database """
import time
import psutil # https://github.com/giampaolo/psutil


class SysPlugin(MymonPlugin):
    def __init__(self):
        self.started = False
        self.proc_timer = None

    def start(self, reqhandler, logger, timer):
        if self.started:
            L.error("System plugin already started")
            return False
        procmon = Procmon()
        self.proc_timer = timer(procmon.monitor, 30000)
        self.proc_timer.start()
        return True

    def stop(self):
        ''' release resources and stop this plugin '''
        pass

    def get_ui_icon_html(self):
        ''' return the raw html for the plugin icon '''
        return '<i class="fa fa-area-chart fa-fw"></i>'

    def get_ui_name(self):
        ''' return the plugin name as it should appear next to the icon '''
        return "System"

    def get_page_name(self):
        '''  Return the name of the html page that corresponds to this plugin '''
        return 'system'


class Procmon(object):
    """ Procmon encapsulates information collection of OS process """
    def __init__(self):
        self.DB = _DB()
        RH.register_ajax_handler('mem_log', self.handle_memlog_req)
        RH.register_ajax_handler('curr_mem', self.handle_currmem_req)
        RH.register_dashboard('mem_dashboard', self.dashboard)

    def dashboard(self):
        """ UI for mympn dashboard """
        return "<br />Procmon plugin UI for dashboard<br />"

    def free_mem(self):
        """ caclulate free memory """
        pass

    def handle_currmem_req(self, user, packet):
        """ process to requset memory snapshot """
        L.info("handle_currmem_req, user="+user.decode('utf-8'))
        totmem = psutil.virtual_memory()
        reply = {"used":totmem.used, "available":totmem.available, "free":totmem.free,}
        return reply

    def handle_memlog_req(self, user, packet):
        """ process the requset we regitered to handle """
        #print("=========" + json.dumps(packet))
        start = packet['start']
        end = packet['end']
        mappings = 'get_mappings' in packet
        pinfo = self.DB.get_proc_info(start, end, mappings)
        minfo = self.DB.get_mem_info(start, end)
        reply = {"pinfo":pinfo, "minfo":minfo}
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
            pcode = self.DB.get_code(name)
            proclist.append((now, pcode, mem))
        self.DB.add_proc_info(proclist)
        totmem = psutil.virtual_memory()
        self.DB.add_total_mem_info(now, totmem.used, totmem.available, totmem.free)

if __name__ == "__main__":
    PRMON = Procmon()
    PRMON.monitor()
