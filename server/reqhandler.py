""" Module that contains the global registration handler """
import json
import os
import inspect
import mmconf
from logger import L

class _RequestHandler(object):
    """ a global object used to register and invoke handlers of requests from web clients"""
    def __init__(self):
        """ initialize container of request handlers """
        self.websock_handlers = {}
        self.ajax_handlers = {'__dashboard__': self.get_dashboard_ui}
        self.dashboard_handlers = {}

    def get_dashboard_ui(self, user, packet):
        """ collect all the dashboard UI from the different components """
        dashboard_ui = []
        plugins_order = mmconf.OPT['plugins_order']
        for plugin in self.dashboard_handlers:
            puipos = 999999
            plugins_order = mmconf.OPT['plugins_order']
            if plugin in plugins_order:
                puipos = plugins_order[plugin]
            if puipos != 0:
                html = self.dashboard_handlers[plugin]()
                try:
                    html = html.decode('utf-8')
                except AttributeError:
                    pass
                dashboard_elem = {"uipos":puipos, "name":plugin, "html":html}
                dashboard_ui.append(dashboard_elem)
        dashboard_ui.sort(key=lambda o: o['uipos'])
        return {"dashboard_ui":dashboard_ui}

    def register_dashboard(self, function):
        """ add a dashboard function for a monitoring component """

        plugin_file = None
        frame = inspect.stack()[1]

        if hasattr(frame, 'filename'):
            # Changed from Python 3.5
            plugin_file = os.path.basename(os.path.normpath(frame.filename))
        else:
            plugin_file = os.path.basename(os.path.normpath(frame[1]))

        plugin_name = plugin_file.split(".")[0]
        if plugin_name in self.dashboard_handlers:
            L.error("Error:" + plugin_name + " is already in dashboard")
            return False
        self.dashboard_handlers[plugin_name] = function
        return True

    def register_ajax_handler(self, request, function):
        """ component registers its ajax requests handlers via this method"""
        if request in self.ajax_handlers:
            L.error("Error: request:" + request + " is already registered")
            return False
        self.ajax_handlers[request] = function
        L.info("registered:"+request)
        return True

    def ajax_request(self, user, packet):
        """ invoke the appropriate method of the designated request handler """
        request = packet["request"]
        if not request in self.ajax_handlers:
            L.error("Error: request " + request + " does not have a handler")
            return {"status":"error", "msg":"no handler for "+request}
        reply = self.ajax_handlers[request](user, packet)
        reply['reply-to'] = request
        if 'ctx' in packet:
            # if context received with request, return it unchanged
            reply['ctx'] = packet['ctx']
        return reply

    def register_websock_handlers(self, service, new_client, new_message, close_client):
        """ component registers its websocket requests handlers via this method
            The new_client method should return False if there is a problem
            servicing a new client, otherwise True """
        if service in self.websock_handlers:
            L.error("Error: service:" + service + " is already registered")
            return False
        handlers = {
            "new_client":new_client,
            "new_message":new_message,
            "close_client":close_client
        }
        self.websock_handlers[service] = handlers
        return True

    def websock_new_connection(self, user, client, service):
        """ Notify handler of new client """
        if not service in self.websock_handlers:
            L.error("Error: service:" + service + " not found for new connection")
            return False
        return self.websock_handlers[service]['new_client'](user, client)

    def websock_message(self, user, client, message):
        """ invoke the appropriate method of the designated websock request handler """
        service = client.service
        self.websock_handlers[service]['new_message'](user, client, message)
        return

    def websock_close_connection(self, client):
        """ Notify handler of client closing a connection """
        service = client.service
        if not service in self.websock_handlers:
            L.error("Error: service:" + service + " not found for close connection")
            return
        self.websock_handlers[service]['close_client'](client)


RH = _RequestHandler()
