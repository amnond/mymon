"""
Interface for database related actions
"""
# -*- coding: utf-8 -*-

import os
import sys
import copy
import sqlite3 as lite

class _DB(object):
    """ The DB object which serves as the interface to sqlite operaations """
    def __init__(self):
        self.name2code = {}
        self.code2name = {}
        self.new_mappings_for_db = []
        self.new_mappings_for_web_client = {}
        create_procinfo_table = "CREATE TABLE IF NOT EXISTS procinfo \
                                  ( `utime`  INTEGER, \
                                    `prcode` INTEGER, \
                                    `memory` INTEGER ) "

        create_idx_time = "CREATE INDEX IF NOT EXISTS `idx_time` ON `procinfo` (`utime` ) "
        create_idx_mem = "CREATE INDEX IF NOT EXISTS `idx_mem` ON `procinfo` (`memory` ) "

        create_prcode2name_table = "CREATE TABLE IF NOT EXISTS prcode2name \
                                      ( `prcode` INTEGER, \
                                        `name`   TEXT )"

        get_proc_codes = "SELECT * FROM prcode2name"

        try:
            dbpath = os.path.realpath(__file__)
            dbname = os.path.dirname(dbpath) + '/mon.db'
            print(dbname)
            self.con = lite.connect(dbname)
            self.con.isolation_level = None
            cur = self.con.cursor()
            cur.execute(create_procinfo_table)
            cur.execute(create_idx_time)
            cur.execute(create_idx_mem)
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
                    print(errmsg % (code, self.code2name[code], name))
                else:
                    self.code2name[code] = name

                if name in self.name2code:
                    errmsg = "Table integrity error: "
                    errmsg += "name2code['%s'] already is mapped to %d, cant assign %d"
                    print(errmsg % (name, self.name2code[name], code))
                else:
                    self.name2code[name] = code

        except lite.Error, err:
            print "Error %s:" % err.args[0]
            sys.exit(1)

    def close(self):
        """ Closes the connection """
        if self.con:
            self.con.close()

    def get_name(self, code):
        """Given a process unique code, return it's name"""
        if not code in self.code2name:
            print("Error: no name for code %d:" % (code))
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
            print("add_proc_info failed!")
            cur.execute("rollback")
        self.new_mappings_for_db = []

    def get_proc_info(self, start_time, end_time, mapping):
        """-----------------------------------------------
        Input: time range for process info
        Returns: tuples of time, process name, memory used
        """
        period = (start_time, end_time)
        cur = self.con.cursor()
        query = "SELECT utime, prcode, memory \
                 FROM procinfo WHERE utime >= ? AND utime <= ? \
                 ORDER BY utime DESC \
                 LIMIT 5000"
        cur.execute(query, period)
        rows = cur.fetchall()
        new_mappings = copy.deepcopy(self.new_mappings_for_web_client)
        self.new_mappings_for_web_client = {}
        reply = {"processes":rows, "new_mappings":new_mappings}
        if mapping:
            reply["mappings"] = self.code2name
        return reply


DB = _DB()
