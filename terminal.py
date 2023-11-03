from colors import Colors

class Listener:
    def __init__(self, event, callback):
        self.event = event
        self.callback = callback
class Terminal:
    def __init__(self,base_dir="~",sub_dirs = {}):
        self.dir = base_dir
        self.sub_dirs = sub_dirs
    def cmd_ls(self):
        print(f"Content of \"{Colors.BLUE}"+self.dir+f"{Colors.END}\" :")
        for i in self.sub_dirs.keys():
            print(f"  {Colors.GREEN} -- {Colors.BLUE}{i}")
    def handle_input(self,inp):pass
    def print(self):pass