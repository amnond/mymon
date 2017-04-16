import pluginclass

class hello_plugin(pluginclass.pluginclass):
    def func1(self):
        print("I am hello plugin")

class classname(pluginclass.pluginclass):
    def func1(self):
        print("called from classname/hello")
