''' interface to logger '''
import sys
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
L = logging.getLogger('mymon')
