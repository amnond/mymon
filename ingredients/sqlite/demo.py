#!/usr/bin/python
# -*- coding: utf-8 -*-

# http://zetcode.com/db/sqlitepythontutorial/

import sqlite3 as lite
import sys

con = None

try:
    con = lite.connect('test.db')
    
    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')
    
    data = cur.fetchone()
    
    print "SQLite version: %s" % data                
    

    con = lite.connect('test.db')

    with con:
        
        cur = con.cursor()    
        cur.execute("CREATE TABLE Cars(Id INT, Name TEXT, Price INT)")
        cur.execute("INSERT INTO Cars VALUES(1,'Audi',52642)")
        cur.execute("INSERT INTO Cars VALUES(2,'Mercedes',57127)")
        cur.execute("INSERT INTO Cars VALUES(3,'Skoda',9000)")
        cur.execute("INSERT INTO Cars VALUES(4,'Volvo',29000)")
        cur.execute("INSERT INTO Cars VALUES(5,'Bentley',350000)")
        cur.execute("INSERT INTO Cars VALUES(6,'Citroen',21000)")
        cur.execute("INSERT INTO Cars VALUES(7,'Hummer',41400)")
        cur.execute("INSERT INTO Cars VALUES(8,'Volkswagen',21600)")


        cars = (
            (1, 'Audi', 52642),
            (2, 'Mercedes', 57127),
            (3, 'Skoda', 9000),
            (4, 'Volvo', 29000),
            (5, 'Bentley', 350000),
            (6, 'Hummer', 41400),
            (7, 'Volkswagen', 21600)
        )

    
        cur.execute("DROP TABLE IF EXISTS Cars2")
        cur.execute("CREATE TABLE Cars2(Id INT, Name TEXT, Price INT)")
        cur.executemany("INSERT INTO Cars2 VALUES(?, ?, ?)", cars)

    
        cur = con.cursor()    
        cur.execute("SELECT * FROM Cars")

        while True:
          
            row = cur.fetchone()
            
            if row == None:
                break
                
            print row[0], row[1], row[2]


except lite.Error, e:
    
    print "Error %s:" % e.args[0]
    sys.exit(1)
    
finally:
    
    if con:
        con.close()
