from mmplugin import MymonPlugin

class MyOtherPlugin(MymonPlugin):
    def get_ui_name(self):
        return "Plugin2"

    def get_ui_icon_html(self):
        pass
