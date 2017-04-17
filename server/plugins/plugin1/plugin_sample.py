from mmplugin import MymonPlugin

class MyPlugin(MymonPlugin):
    def get_ui_name(self):
        return "Plugin1"

    def get_ui_icon_html(self):
        pass
