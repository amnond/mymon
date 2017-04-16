"""
The web service implemented via Tornado
"""
#-*- coding:utf-8 -*-

import os.path
import time
import json
import zlib
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.options

#--------------------------------------------
# TODO: Should be read from plugin directory

from procmon import Procmon
from webtail import WebTail
#--------------------------------------------

from reqhandler import RH
from logger import L

# http://guillaumevincent.com/2013/02/12/Basic-authentication-on-Tornado-with-a-decorator.html


class BaseHandler(tornado.web.RequestHandler):
    """ Tornado Base """
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    """ Tornado Main """
    @tornado.web.authenticated
    def get(self):
        host = self.request.host
        self.render('index.html', host=host)

class PageHandler(BaseHandler):
    """ Tornado Specific page """
    @tornado.web.authenticated
    def get(self, url):
        try:
            self.render(url)
        except IOError:
            self.write("Page not found.")

# pylint: disable=C0301
#http://stackoverflow.com/questions/31939132/pylint-complains-about-method-data-received-not-overridden-for-requesthandler

# pylint: disable=W0223
class WebsockHandler(tornado.websocket.WebSocketHandler):
    ''' A websocket connection '''
    def initialize(self, app):
        ''' remember who the web app is '''
        L.info("initializing WebsockHandler")
        self.app = app

    def open(self):
        L.info("WebsockHandler open")
        user = self.get_secure_cookie("user")
        L.info("user="+user)
        self.app.on_open_websock(self, user)

    def on_message(self, message):
        user = self.get_secure_cookie("user")
        L.info("user="+user)
        self.app.on_msg_websock(self, user, message)

    def on_close(self):
        self.app.on_close_websock(self)


class AjaxHandler(BaseHandler):
    """ Tornado Ajax """
    @tornado.web.authenticated
    def post(self):
        spacket = self.get_argument("packet")
        packet = {}
        try:
            packet = json.loads(spacket)
        except ValueError:
            L.error("Error: packet not valid json:" + spacket)

        if "request" not in packet:
            L.error("Error: Received packet without request:" + spacket)
            return

        user = self.get_current_user()
        reply = RH.ajax_request(user, packet)
        response = json.dumps(reply)
        #self.write(response)

        self.set_header("Content-type", 'text/plain')
        self.set_header("Content-Encoding", 'gzip')
        t_1 = time.time()
        gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
        content = gzip_compress.compress(response) + gzip_compress.flush()
        L.info("compression time:%f" % (time.time()-t_1))

        compressed_content_length = len(content)
        self.set_header("Content-Length", compressed_content_length)
        self.write(content)

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

        L.info("%s,%s\n" % (getusername, getpassword))

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
    """ logging out handler """
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", self.reverse_url("main")))


class Application(tornado.web.Application):
    """ Initialize Tornado settings """
    def __init__(self):
        self.listeners = []
        base_dir = os.path.dirname(__file__)
        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "login_url": "/login",
            'template_path': os.path.join(base_dir, "templates"),
            'static_path': os.path.join(base_dir, "static"),
            "static_url_prefix": "/res/",
            'debug': True,
            "xsrf_cookies": True
        }

        settings['compress_response'] = True

        tornado.web.Application.__init__(self, [
            tornado.web.url(r"/(favicon\.ico)", tornado.web.StaticFileHandler),
            tornado.web.url(r"/", MainHandler, name="main"),
            tornado.web.url(r"/(.*\.html)", PageHandler, name="mymon"),
            tornado.web.url(r'/login', LoginHandler, name="login"),
            tornado.web.url(r'/logout', LogoutHandler, name="logout"),
            tornado.web.url(r"/ajax", AjaxHandler, name="ajax"),
            tornado.web.url(r"/websock/", WebsockHandler, dict(app=self), name="websock"),
        ], **settings)

    def on_open_websock(self, client, user):
        """ new websoock has connected """
        self.listeners.append(client)
        L.info("websock connected")

    def on_close_websock(self, client):
        """ existing websoock has been closed """
        self.listeners.remove(client)
        if len(self.listeners) == 0:
            pass
        L.info("websock closed")
        if hasattr(client, "service"):
            RH.websock_close_connection(client)

    def on_msg_websock(self, client, user, message):
        """ new message from existing websock """
        L.info("websock message:" + message)
        if not hasattr(client, "service"):
            # first time we hear from this connection (i.e service request)
            packet = {}
            try:
                packet = json.loads(message)
            except ValueError:
                errstr = "websock initial packet not valid json"
                L.error(errstr)
                reply = {"status":"error", "msg":errstr}
                client.write_message(json.dumps(reply))
                return
            if 'service' not in packet:
                errstr = "no service specification in request"
                reply = {"status":"error", "msg":errstr}
                client.write_message(json.dumps(reply))
                return
            service = packet['service']
            if not RH.websock_new_connection(user, client, service):
                msg = "service " + service + " unavailable"
                L.error(msg)
                reply = {"status":"error", "msg":msg}
                client.write_message(json.dumps(reply))
                return
            reply = {"status":"ok", "msg":"Service accepted", "service":service}
            client.write_message(json.dumps(reply))
            client.service = service
            return

        RH.websock_message(user, client, message)

class Web(object):
    """ The interface to the Web service from the mymon daemon """
    def __init__(self):
        self.port = 8888
        self.proc_timer = None
        self.tail_timer = None
        self.sinterval = 15 * 60 * 1000

    def set_config(self, conf):
        """ Set various web server settings """
        if 'port' in conf:
            self.port = conf.port

        if 'proc_scan_interval' in conf:
            self.sinterval = conf.proc_scan_interval

    def ioloop(self):
        """ The Tornado event loop """
        #------------------------------------------------
        # TODO: Should be activated from plugin directory
        webtail = WebTail()
        procmon = Procmon()
        #------------------------------------------------

        #------------------------------------------------
        # TODO: Should be timer service per plugon
        self.tail_timer = tornado.ioloop.PeriodicCallback(webtail.follow, 1000)
        self.tail_timer.start()

        self.proc_timer = tornado.ioloop.PeriodicCallback(procmon.monitor, self.sinterval)
        self.proc_timer.start()
        #------------------------------------------------

        Application().listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    WEB = Web()
    WEB.ioloop()
