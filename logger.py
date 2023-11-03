from colorama import Fore, Back, Style, init
import sys
from datetime import datetime as dt




init()

class Logger:
    def __init__(self,master):
        self.master = master
        
    def debug(self,*text,end='\n'):
        print(Style.BRIGHT+Fore.BLUE+"["+self.time()+"] [&] "+str(self.master)+": ",end='')
        for value in text:
            print(value,end=' ')
        print(Style.RESET_ALL,end=end)   
    def info(self,*text,end='\n'):
        print(Style.BRIGHT+Fore.GREEN+"["+self.time()+"] [+] "+str(self.master)+": ",end='')
        for value in text:
            print(value,end=' ')
        print(Style.RESET_ALL,end=end)
    
    def warning(self,*text,end='\n'):
        print(Style.BRIGHT+Fore.YELLOW+"["+self.time()+"] [*] "+str(self.master)+": ",end='')
        for value in text:
            print(value,end=' ')
        print(Style.RESET_ALL,end=end)
        
    def error(self,*text,end='\n'):
        print(Style.BRIGHT+Fore.RED+"["+self.time()+"] [!] "+str(self.master)+": ",end='')
        for value in text:
            print(value,end=' ')
        print(Style.RESET_ALL,end=end)
    
    def critical(self,*text,end='\n'):
        print(Style.BRIGHT+Fore.RED+"["+self.time()+"] [-] "+str(self.master)+": ",end='')
        for value in text:
            print(value,end=' ')
        print(Style.RESET_ALL,end=end)
        
    def time(self):
        date = dt.now()
        return date.strftime("%d/%m/%Y %H:%M:%S")




if __name__ == '__main__':
    log = Logger("Test")
    log.debug("Debug message")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")
    log.critical("Critical message")