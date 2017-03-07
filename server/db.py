# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys

class DB:
    def __init__(self):
        create = "CREATE TABLE IF NOT EXISTS procinfo \
              ( `utime` INTEGER, \
                `name` TEXT, \
                `memory` INTEGER ) "

        create_mi = "CREATE INDEX IF NOT EXISTS `idx_mem` ON `procinfo` (`utime` ) "

        try:
            dbname = '/Users/amnondavid/projects/mymon/server/mon.db'
            self.con = lite.connect(dbname)
            self.con.isolation_level = None
            cur = self.con.cursor()
            cur.execute(create)
            cur.execute(create_mi)
        except lite.Error, e:
            print "Error %s:" % e.args[0]
            sys.exit(1)


    def close(self):
        if self.con:
            self.con.close()

    """-----------------------------------------------
    Input: tuples of (time. process name, memory used)
    """
    def add_proc_info(self, proc_info):
        try:
            cur = self.con.cursor()
            cur.execute("begin")
            cur.executemany("INSERT INTO procinfo VALUES(?, ?, ?)", proc_info)
            cur.execute("commit")
        except self.con.Error:
            print("add_proc_info failed!")
            cur.execute("rollback")

    """-----------------------------------------------
    Input: time range for process info
    Returns: tuples of time, process name, memory used
    """
    def get_proc_info(self, start_time, end_time):
        period = (start_time, end_time)
        cur = self.con.cursor()
        query = "SELECT * FROM procinfo WHERE utime >= ? AND utime <= ?"
        cur.execute(query, period)
        rows = self.cur.fetchall()
        return rows
