from mmplugin import MymonPlugin

class MyPlugin(MymonPlugin):
    def start(self, reqhandler, logger, timer):
        '''  initialize this plugin '''
        pass

    def stop(self):
        ''' release resources and stop this plugin '''
        pass

    def get_ui_icon_html(self):
        ''' return the raw html for the plugin icon '''
        return '<i class="fa fa-cog fa-fw"></i>'

    def get_ui_name(self):
        ''' return the plugin name as it should appear next to the icon '''
        return "Plugin1"

    def get_page_name(self):
        '''  Return the name of the html page that corresponds to this plugin '''
        return 'plugin_sample'
    