# Linux requirements:

## For the Mymon framework
    * pip install tornado

## For user authentication
    * pip install bcrypt
    * pip install dataset

## Required for the system plugin for system diagnostic info (memory, cpu, disk etc.)
    * pip install psutil

    For SQLite support on Python 2:
    * sudo apt-get install sqlite3
    * sudo apt-get install libsqlite3-dev
    * sudo pip install pysqlite