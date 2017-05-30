"""
Interface for database related actions
"""
# -*- coding: utf-8 -*-

import os
import sys
import copy
import sqlite3 as lite

import time

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
L = logging.getLogger('system/db')


class _DB(object):
    """ The DB object which serves as the interface to sqlite operaations """
    def __init__(self):
        self.name2code = {}
        self.code2name = {}
        self.new_mappings_for_db = []
        self.new_mappings_for_web_client = {}

        create_totalmem_table = "CREATE TABLE IF NOT EXISTS totalmem \
                                  ( `utime`  INTEGER, \
                                    `used` INTEGER, \
                                    `avail` INTEGER, \
                                    `free` INTEGER ) "

        create_procinfo_table = "CREATE TABLE IF NOT EXISTS procinfo \
                                  ( `utime`  INTEGER, \
                                    `prcode` INTEGER, \
                                    `memory` INTEGER ) "

        create_idx_time = "CREATE INDEX IF NOT EXISTS `idx_time` ON `procinfo` (`utime` ) "
        create_idx_mem = "CREATE INDEX IF NOT EXISTS `idx_mem` ON `procinfo` (`memory` ) "

        create_idx_tmem = "CREATE INDEX IF NOT EXISTS `idx_mtime` ON `totalmem` (`utime` ) "

        create_prcode2name_table = "CREATE TABLE IF NOT EXISTS prcode2name \
                                      ( `prcode` INTEGER, \
                                        `name`   TEXT )"

        get_proc_codes = "SELECT * FROM prcode2name"

        try:
            dirname = os.path.dirname(os.path.realpath(__file__))
            dbname = os.path.join(dirname, 'mon.db')
            L.info(dbname)
            self.con = lite.connect(dbname)
            self.con.isolation_level = None
            cur = self.con.cursor()
            cur.execute(create_procinfo_table)
            cur.execute(create_idx_time)
            cur.execute(create_idx_mem)

            cur.execute(create_totalmem_table)
            cur.execute(create_idx_tmem)

            cur.execute(create_prcode2name_table)

            cur.execute(get_proc_codes)
            rows = cur.fetchall()
            total = len(rows)
            self.next_proc_code = total
            for i in range(0, total):
                row = rows[i]
                # TODO: would prefer to access column by name
                code = row[0]
                name = row[1]
                if code in self.code2name:
                    errmsg = "Table integrity error: "
                    errmsg += "code2name[%d] already is mapped to %s, cant assign %s"
                    err = errmsg % (code, self.code2name[code], name)
                    L.error(err)
                else:
                    self.code2name[code] = name

                if name in self.name2code:
                    errmsg = "Table integrity error: "
                    errmsg += "name2code['%s'] already is mapped to %d, cant assign %d"
                    err = errmsg % (name, self.name2code[name], code)
                    L.error(err)
                else:
                    self.name2code[name] = code

        except lite.Error as err:
            error = "Error %s:" % err.args[0]
            L.error(error)
            sys.exit(1)

    def close(self):
        """ Closes the connection """
        if self.con:
            self.con.close()

    def get_name(self, code):
        """Given a process unique code, return it's name"""
        if not code in self.code2name:
            err = "Error: no name for code %d:" % (code)
            L.error(err)
            return ""
        return self.code2name[code]

    def get_code(self, name):
        """Given a process name, return it's unique code"""
        if not name in self.name2code:
            # this is a new process name. Create a code for it and add it
            self.next_proc_code += 1
            self.name2code[name] = self.next_proc_code
            self.code2name[self.next_proc_code] = name
            self.new_mappings_for_db.append((self.next_proc_code, name))
            self.new_mappings_for_web_client[self.next_proc_code] = name
            return self.next_proc_code
        return self.name2code[name]

    def add_total_mem_info(self, utime, used, avail, free):
        """
        Input: tuples of (time. used memory, available memory)
        Adds new memory info to history
        """
        try:
            cur = self.con.cursor()
            cur.execute("begin")
            cur.execute("INSERT INTO totalmem VALUES(?, ?, ?, ?)", (utime, used, avail, free))
            cur.execute("commit")
        except self.con.Error:
            L.error("add_total_mem_info failed!")
            cur.execute("rollback")

    def add_proc_info(self, procs_info):
        """
        Input: tuples of (time. process name, memory used)
        Adds new process info to history, updates process code mappings
        """
        try:
            cur = self.con.cursor()
            cur.execute("begin")
            if len(self.new_mappings_for_db):
                cur.executemany("INSERT INTO prcode2name VALUES(?, ?)", self.new_mappings_for_db)
            cur.executemany("INSERT INTO procinfo VALUES(?, ?, ?)", procs_info)
            cur.execute("commit")
        except self.con.Error:
            L.error("add_proc_info failed!")
            cur.execute("rollback")
        self.new_mappings_for_db = []

    def get_mem_info(self, start_time, end_time):
        """-----------------------------------------------
        Input: time range for total memory info
        Returns: tuples of time, used memory, free memory
        """

        t_1 = time.time()
        params = (start_time, start_time, end_time)
        cur = self.con.cursor()
        query = "SELECT utime-?, used, avail, free \
                 FROM totalmem \
                 WHERE utime >= ? AND utime <= ?"

        cur.execute(query, params)
        rows = cur.fetchall()
        reply = {"start_time":start_time, "totalmem":rows}
        dbg = "mem_query => rows: %d, qtime:%f" % (len(rows), time.time()-t_1)
        L.debug(dbg)
        return reply

    def get_proc_info(self, start_time, end_time, mapping):
        """-----------------------------------------------
        Input: time range for process info
        Returns: tuples of time, process name, memory used
        """
        # timer_period = 15000
        # samples = 30
        # period_for_avg = (end_time-samples*(timer_period/1000), end_time)

        period_for_avg = (end_time-int(end_time-start_time/10), end_time)

        cur = self.con.cursor()

        t_1 = time.time()

        # get ids of top 10 memory consumers in the given period
        query = "SELECT prcode \
                 FROM procinfo \
                 WHERE utime >= ? AND utime <= ? \
                 GROUP BY prcode \
                 ORDER BY avg(memory) desc \
                 LIMIT 10"
        dbg = "avg calc: %f" % (time.time()-t_1)
        L.debug(dbg)

        t_1 = time.time()

        cur.execute(query, period_for_avg)
        rows_mem = cur.fetchall()
        mem_order = [row[0] for row in rows_mem]
        id_by_mem = ",".join([str(mem) for mem in mem_order])

        params = (start_time, start_time, end_time)

        query = "SELECT utime-?, prcode, memory \
                 FROM procinfo \
                 WHERE \
                    utime >= ? AND utime <= ? AND \
                    prcode in ("+id_by_mem+")"

        cur.execute(query, params)
        rows = cur.fetchall()
        new_mappings = copy.deepcopy(self.new_mappings_for_web_client)
        self.new_mappings_for_web_client = {}
        reply = {"processes":rows,
                 "start_time":start_time,
                 "memorder":mem_order,
                 "new_mappings":new_mappings}
        if mapping:
            reply["mappings"] = self.code2name

        dbg = "proc_query => rows: %d, qtime:%f" % (len(rows), time.time()-t_1)
        L.debug(dbg)
        return reply
