"""
The web service implemented via Tornado
"""
#-*- coding:utf-8 -*-

import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from procmon import Procmon

class BaseHandler(tornado.web.RequestHandler):
    """ Tornado Base """
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    """ Tornado Main """
    @tornado.web.authenticated
    def get(self):
        self.render('index.html')

class LoginHandler(BaseHandler):
    """ Tornado attempt to get page if authenticated """
    @tornado.gen.coroutine
    def get(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return
        self.render('login.html')

    @tornado.gen.coroutine
    def post(self):
        """ Tornado post authentication credentials """
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return

        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))

        print("%s,%s\n" % (getusername, getpassword))

        if getusername == "demo" and getpassword == "demo":
            self.set_secure_cookie("user", self.get_argument("username"))
            self.set_secure_cookie("incorrect", "0")
            self.redirect(self.reverse_url("main"))
        else:
            incorrect = self.get_secure_cookie("incorrect") or 0
            increased = str(int(incorrect)+1)
            self.set_secure_cookie("incorrect", increased)
            self.write("""<center>
                            Something Wrong With Your Data (%s)<br />
                            <a href="/">Go Home</a>
                          </center>""" % increased)


class LogoutHandler(BaseHandler):
    """ logging hout handler """
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", self.reverse_url("main")))

class Application(tornado.web.Application):
    """ Initialize Tornado settings """
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "login_url": "/login",
            'template_path': os.path.join(base_dir, "templates"),
            'static_path': os.path.join(base_dir, "static"),
            'debug':True,
            "xsrf_cookies": True,
        }

        tornado.web.Application.__init__(self, [
            tornado.web.url(r"/", MainHandler, name="main"),
            tornado.web.url(r'/login', LoginHandler, name="login"),
            tornado.web.url(r'/logout', LogoutHandler, name="logout"),
        ], **settings)

class Web(object):
    """ The interface to the Web service from the mymon daemon """
    def __init__(self):
        self.port = 8888
        self.proc_timer = None
        self.sinterval = 20000

    def set_config(self, conf):
        """ Set various web server settings """
        if 'port' in conf:
            self.port = conf.port

        if 'proc_scan_interval' in conf:
            self.sinterval = conf.proc_scan_interval

    def ioloop(self):
        """ The Tornado event loop """
        procmon = Procmon()
        self.proc_timer = tornado.ioloop.PeriodicCallback(procmon.monitor, self.sinterval)
        self.proc_timer.start()
        Application().listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    WEB = Web()
    WEB.ioloop()
