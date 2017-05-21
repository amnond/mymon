from mmplugin import MymonPlugin

class MyOtherPlugin(MymonPlugin):
    def get_ui_icon_html(self):
        ''' return the raw html for the plugin icon '''
        return '<i class="fa fa-pencil fa-fw"></i>'

    def get_ui_name(self):
        ''' return the plugin name as it should appear next to the icon '''
        return "Plugin2"

    def get_page_name(self):
        '''  Return the name of the html page that corresponds to this plugin '''
        return 'plugin_sample_2'
