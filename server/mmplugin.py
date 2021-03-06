'''
Mymon plugin class API
'''

class MymonPlugin(object):
    '''
    An abstract Mymon plugin class. This should be subclassed in order to
    implement a Mymon plugin
    '''
    def start(self, reqhandler, logger, timer):
        '''  initialize this plugin '''
        pass

    def stop(self):
        ''' release resources and stop this plugin '''
        pass

    def get_ui_icon_html(self):
        '''  Return the html code that generates an icon which represents this plugin '''
        pass

    def get_ui_name(self):
        ''' Return the name of the plugin as it should appear in the Web UI '''
        return "noname"

    def get_page_name(self):
        '''  Return the name of the html page that corresponds to this plugin '''
        pass
