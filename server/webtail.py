""" Process monitor: scans processes and sends status to database """
import time

from reqhandler import RH
from logger import L

class WebTail(object):
    """ WebTail handles log files to monitor """
    def __init__(self):
        self.filenames = ['/Users/amnondavid/projects/mymon/server/test.txt']
        self.tailed_files = []
        RH.register_websock_handlers('webtail',
                                     self.new_client,
                                     self.new_message,
                                     self.close_client)

    def new_client(self, client):
        """ invoked whenever a new client joins the service webtail"""
        L.info("received new client")
        return True

    def new_message(self, client, message):
        """ invoked whenever a client sends a new message to service webtail"""
        L.info("received new message:"+message)
        client.write_message("hello from server")

    def close_client(self, client):
        """ invoked whenever a new client joins the service webtail"""
        L.info("webtail - client closed")
