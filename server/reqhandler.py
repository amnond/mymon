""" Module that contains the global registration handler """
import json

class _RequestHandler(object):
    """ a global object used to register and invoke handlers of requests from web clients"""
    def __init__(self):
        """ initialize container of request handlers """
        self.request_handlers = {'__dashboard__': self.get_dashboard_ui}
        self.dashboard_handlers = {}

    def get_dashboard_ui(self, packet):
        """ collect all the dashboard UI from the different components """
        html = '<h5>Mymon Dashboard</h5><hr />'
        for handler in self.dashboard_handlers:
            html += self.dashboard_handlers[handler]()
        return {"html":html}

    def register_dashboard(self, request, function):
        """ add a dashboard function for a monitoring component """
        if request in self.dashboard_handlers:
            print("Error: request:" + request + " is already registered")
            return False
        self.dashboard_handlers[request] = function
        return True

    def register_handler(self, request, function):
        """ event monitoring compoenent registers it's requests handlers via this method"""
        if request in self.request_handlers:
            print("Error: request:" + request + " is already registered")
            return False
        self.request_handlers[request] = function
        return True

    def invoke(self, packet):
        """ invoke the appropriate method of the designated request handler """
        request = packet["request"]
        if not request in self.request_handlers:
            print("Error: request " + request + " does not have a handler")
            return {"status":"error", "msg":"no handler for "+request}
        reply = self.request_handlers[request](packet)
        reply['reply-to'] = request
        if 'ctx' in packet:
            # if context received with request, return it unchanged
            reply['ctx'] = packet['ctx']
        return reply


RH = _RequestHandler()
