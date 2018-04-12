# MyMon

#### a Tornado based, plugin-extendible system diagnostics service
* Lightweight service
* Historical tracking of system resource usage (memory, processes, network, cpu etc.)
* Web browser as client
* Easily extendible on both server and client
* Supports either Python 2.x or Python 3.x 

The project was dormant for a while before being moved to github. The current license is GPL. Documentation on use and architecture will gradually be added.

### Linux requirements:
```
sudo apt install unzip
sudo apt install python-pip
pip install --upgrade pip
```
### For the Mymon framework
```
sudo pip install tornado
```

### For user management + authentication (as yet unused)
```
sudo pip install bcrypt
sudo pip install dataset
```

### Required for the system plugin for system diagnostic info (memory, cpu, disk etc.)
```
sudo pip install psutil, which requires:
    For apt (ubuntu, debian...)
        sudo apt-get install python-dev
               or
        sudo apt-get install python3-dev
    For yum (centos, redhat, fedora...)
        sudo yum install python-devel

    For SQLite support on Python 2:
        sudo apt-get install sqlite3
        sudo apt-get install libsqlite3-dev
        sudo pip install pysqlite
```

## File heirarchy example
```
├── plugins
│   ├── system
│   │   ├── db.py
│   │   ├── mon.db
│   │   ├── static
│   │   │   ├── css
│   │   │   │   ├── daterangepicker.css
│   │   │   │   └── vis-timeline-graph2d.min.css
│   │   │   └── js
│   │   │       ├── daterangepicker.js
│   │   │       ├── gauge.min.js
│   │   │       ├── jquery-resizable.min.js
│   │   │       └── vis-timeline-graph2d.min.js
│   │   ├── system.py
│   │   ├── system_dashboard.html
│   │   └── templates
│   │       └── system.html
│   └── webtail
│       ├── static
│       │   ├── css
│       │   │   └── bootstrap-colorpicker.min.css
│       │   └── js
│       │       ├── bootstrap-colorpicker.js
│       │       └── mindmup-editabletable.js
│       ├── templates
│       │   └── webtail.html
│       ├── webtail.json
│       ├── webtail.py
├── static
│   ├── css
│   │   ├── bootstrap-theme.min.css
│   │   ├── bootstrap.min.css
│   │   ├── css_animation.css
│   │   ├── font-awesome.min.css
│   │   ├── metisMenu.min.css
│   │   └── sb-admin-2.css
│   ├── img
│   │   ├── ajax-loader.gif
│   │   ├── color-splash.jpg
│   │   ├── mymon.png
│   │   └── mymon_red.png
│   ├── js
│   │   ├── bootbox.min.js
│   │   ├── bootstrap.min.js
│   │   ├── bootstrap.modal.wrapper.js
│   │   ├── client-framework.js
│   │   ├── jquery-3.1.1.min.js
│   │   ├── metisMenu.min.js
│   │   ├── moment.min.js
│   │   ├── sb-admin-2.js
│   │   └── utils.js
│   └── plugins
│       ├── system
│       │   ├── css
│       │   │   ├── daterangepicker.css
│       │   │   └── vis-timeline-graph2d.min.css
│       │   └── js
│       │       ├── daterangepicker.js
│       │       ├── gauge.min.js
│       │       ├── jquery-resizable.min.js
│       │       └── vis-timeline-graph2d.min.js
│       └── webtail
│           ├── css
│           │   └── bootstrap-colorpicker.min.css
│           └── js
│               ├── bootstrap-colorpicker.js
│               └── mindmup-editabletable.js
├── templates
    ├── dashboard.html
    ├── index.html
    ├── login.html
    └── plugins
        ├── system
        │   └── system.html
        └── webtail
            └── webtail.html
```
