""" Module that contains the global registration handler """
import json

class _RequestHandler(object):
    """ a global object used to register and invoke handlers of requests from web clients"""
    def __init__(self):
        """ initialize container of request handlers """
        self.request_handlers = {}

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
        return self.request_handlers[request](packet)

RH = _RequestHandler()
