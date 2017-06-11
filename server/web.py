"""
The web service implemented via Tornado
"""
#-*- coding:utf-8 -*-
import sys

import os.path
import time
import json
# import distutils
# from distutils import dir_util
import shutil
import inspect
import zlib
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.options

import loadmodule
from mmplugin import MymonPlugin

from reqhandler import RH
from logger import L

import mmconf

if mmconf.OPT['DEBUG']:
    import tornado.autoreload

def fopen(filename, opt):
    ver = sys.version_info.major
    if ver < 3:
        return file(filename, opt)
    return open(filename, opt)

# http://guillaumevincent.com/2013/02/12/Basic-authentication-on-Tornado-with-a-decorator.html

def copy_plugins_client_files():
    plugin_js_files = []
    plugin_css_files = []
    ''' copy all plugins html resources to the tornado static resources directory '''
    currdir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(currdir, 'plugins')

    # If the debug flag is on, ask tornado to watch all the plugin development files
    # (including python and html sources) and reload (and thus reload the python plugins
    # as well as recopy the plugins' html files to the mymon static web directory) if
    # any of these files are changed.
    if mmconf.OPT['DEBUG']:
        tornado.autoreload.start()
        ppath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        for root, subdirs, files in os.walk(ppath):
            for file in files:
                wpath = os.path.join(root, file)
                if wpath.endswith((".js", ".css", ".html", ".py")):
                    #L.info(wpath)
                    tornado.autoreload.watch(wpath)

    static_dir = os.path.join(currdir, 'static', 'plugins')
    templates_dir = os.path.join(currdir, 'templates', 'plugins')
    dirlist = os.listdir(plugins_dir)
    for pdir in dirlist:
        plg_path = os.path.join(plugins_dir, pdir)
        if os.path.isdir(plg_path):
            # Plugin directory. Check if it has client resource
            static_path = os.path.join(plg_path, 'static')

            # Collect all the static js and css files used by
            # the various plugins so that they can be included
            # in the index.html template.
            for root, subdirs, files in os.walk(static_path):
                if len(subdirs) == 0:
                    for file in files:
                        fullpath = os.path.join(root, file)
                        webpath = fullpath.replace(currdir + os.sep, '')
                        webpath = webpath.replace('static' + os.sep, '')

                        if file.endswith(".js"):
                            plugin_js_files.append(webpath)
                        elif file.endswith(".css"):
                            plugin_css_files.append(webpath)

            if os.path.isdir(static_path):
                # plugin has html resources. Copy them to tornado static directory
                dst = os.path.join(static_dir, pdir)
                copytree_process(static_path, dst)
                #distutils.dir_util.copy_tree(static_path, dst)

            templates_path = os.path.join(plg_path, 'templates')
            if os.path.isdir(templates_path):
                # plugin has html templates. Copy them to tornado template directory
                dst = os.path.join(templates_dir, pdir)
                copytree_process(templates_path, dst, process_dst)
                #distutils.dir_util.copy_tree(templates_path, dst)

    return (plugin_css_files, plugin_js_files)

def process_dst(dst_path):
    name, ext = os.path.splitext(dst_path)
    if ext not in ('.html', '.htm'):
        return
    with fopen(dst_path, "r") as f1:
        with fopen(dst_path+".tmp", "w") as f2:
            # Make sure source format will remain the same when sent
            # to the client - makes client side debugging easier
            f2.write("{% whitespace all %}\n")
            for line in f1:
                f2.write(line)
    os.remove(dst_path)
    shutil.move(dst_path+".tmp", dst_path)

def copytree_process(src, dst, process=None, symlinks=False):
    names = os.listdir(src)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree_process(srcname, dstname, process, symlinks)
            else:
                shutil.copy2(srcname, dstname)
                if process is not None:
                    process(dstname)

        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    for err in errors:
        L.error(err)
    return len(errors) == 0

def load_plugins():
    ''' Dynamically load and initialize all the Mymon plugins '''
    L.info(" --> loading plugins")
    plugins = []
    currdir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(currdir, 'plugins')
    dirs = [x for x in os.listdir(plugins_dir) \
              if os.path.isdir(plugins_dir+os.sep+x)]
    for dirname in dirs:
        subdir = os.path.join(plugins_dir, dirname)

        # get the UI order for this plugin directory
        pbasedir = os.path.basename(os.path.normpath(subdir))
        puipos = 999999
        plugins_order = mmconf.OPT['plugins_order']
        if pbasedir in plugins_order:
            puipos = plugins_order[pbasedir]

        # Make sure each plugin has import access to the
        # other modules in its directory (for some reason
        # this is sometimes not needed - haven't figured
        # why yet... )
        L.info('   -> ' + subdir)

        if puipos == 0:
            L.info("      ... Skipping plugin (config.json)")
            continue

        sys.path.append(subdir)

        # Go over all the python files in the plugin folder and inspect their
        # classes. and if a class is derived from Mymon plugin, instantiate it
        # and add it to the list of plugins
        # TODO: Make sure that only one MymonPlugin derived class exists within
        #       a plugin directory.
        files = [x for x in os.listdir(subdir) \
                   if os.path.isfile(os.path.join(subdir, x)) and x.endswith(".py")]
        for filename in files:
            plugin_candidate = os.path.join(subdir, filename)
            plugin_module = loadmodule.load_module(plugin_candidate)
            plugin_classes = inspect.getmembers(plugin_module, inspect.isclass)
            modname, extname = os.path.splitext(filename)
            for plugin_class in plugin_classes:
                pcls = plugin_class[1]
                if issubclass(pcls, MymonPlugin) and pcls.__module__ == modname:
                    ipcls = pcls()
                    ipcls.dir = subdir.replace(currdir + os.sep, '')
                    ipcls.uipos = puipos
                    plugins.append(ipcls)
    # Sort the loaded plugins according to their configured UI position
    plugins.sort(key=lambda o: o.uipos)
    return plugins

class BaseHandler(tornado.web.RequestHandler):
    """ Tornado Base """
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    """ Tornado Main """
    def initialize(self, app):
        ''' remember who the web app is '''
        L.info("initializing MainHandler")
        self.app = app

    @tornado.web.authenticated
    def get(self):
        host = self.request.host
        # Authenticated. Render index.html template and pass to the
        # template the parameters of the hos, interfaces of plugins,
        # list of paths for plugin static js and css files.
        self.render('index.html',
                    host=host,
                    plugins=self.app.plugins,
                    plugins_js=self.app.plugin_js_files,
                    plugins_css=self.app.plugin_css_files)

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
        user = self.get_secure_cookie("user").decode('utf-8')
        L.info("user="+user)
        self.app.on_open_websock(self, user)

    def on_message(self, message):
        user = self.get_secure_cookie("user").decode('utf-8')
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

        # convert the reply to JSON and then to bytes
        response = str.encode(json.dumps(reply))

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
            'debug': mmconf.OPT['DEBUG'],
            "xsrf_cookies": True
        }

        settings['compress_response'] = True

        # save the paths of plugins' static css and js files
        self.plugin_css_files, self.plugin_js_files = copy_plugins_client_files()
        # save the interface to the instances of the plugins
        self.plugins = load_plugins()

        tornado.web.Application.__init__(self, [
            tornado.web.url(r"/(favicon\.ico)", tornado.web.StaticFileHandler),
            tornado.web.url(r"/", MainHandler, dict(app=self), name="main"),
            tornado.web.url(r"/(.*\.html)", PageHandler, name="mymon"),
            tornado.web.url(r'/login', LoginHandler, name="login"),
            tornado.web.url(r'/logout', LogoutHandler, name="logout"),
            tornado.web.url(r"/ajax", AjaxHandler, name="ajax"),
            tornado.web.url(r"/websock/", WebsockHandler, dict(app=self), name="websock"),
        ], **settings)

    def init_plugins(self):
        """ call the start method of all the loaded mymon plugins """
        for plugin in self.plugins:
            plugin.start(RH, L, tornado.ioloop.PeriodicCallback)

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

    def set_config(self, conf):
        """ Set various web server settings """
        if 'port' in conf:
            self.port = conf.port

    def ioloop(self):
        """ The Tornado event loop """

        app = Application()
        app.init_plugins()

        app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    WEB = Web()
    WEB.ioloop()
