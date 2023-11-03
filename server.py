import socket
from _thread import *
import threading
import channels as channels_module
import logger
import worker
import time
import tty
import sys
"""
tty.setraw(sys.stdin)

def input(prompt):
    print(prompt,end="")
    while True:
        char = sys.stdin.read(1)
        if ord(char) == 3: # CTRL-C
            break;
        print(ord(char))
        sys.stdout.write(u"\u001b[1000D") # Move all the way left
"""
        
    


log=logger.Logger("[Main server]")
bots = worker.BotGroup("[Main Group]")


def client(sock,addr):
    bot = worker.Bot(sock,"bot",addr,bots)
    bot.channel.set_value("id",bot.id)
    global running
    while 1:
        if not running:
            bot.channel.close()
            bots.remove_bot(bot.id)
            break
        bot.tick()
    
socket.setdefaulttimeout(3)

running = True
server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    server.bind(("localhost",8000))
    server.listen(1000)
    log.info("Binding done.")
except:
    log.error("Adress already in use.")
    server.close()
    exit()
    
    
threads = []
    
def accept_thread():
    log.info("Server started, waiting for conns.")
    while running:
        try:
            sock,addr = server.accept()
            log.info("Connection accepted: "+str(addr))
            th = threading.Thread(target=client,args=(sock,addr))
            threads.append(th)
            th.start()
        except socket.timeout:
            pass
        except Exception as e:
            if running:
                log.critical(str(e))
            try:
                server.shutdown(socket.SHUT_RDWR)
            except:pass
            break

def control_channel(id):
    try:
        channel = bots.bots[id].channel
    except:
        print("This bot dosen't exsist.")
        return
    while 1:
        cmd,*args = input("Bot-"+id+" >  ").split(" ")
        if cmd == "exit":
            break
        elif cmd == "disconnect":
            channel.close()
            bots.remove_bot(id)
        else:
            try:
                r = eval(cmd,{"bot":channel})
                if r is not None:
                    print(r)
            except Exception as e:
                print(e.__class__.__name__+": "+str(e))
start_new_thread(accept_thread,())
time.sleep(0.5)
while 1:
    cmd = input("server >  ")
    if cmd == "exit":
        running=False
        server.close()
        for i in threads:
            i.join()
        log.info("Server stopped")
        break
    if cmd in ["ctrl","control"]:
        id = input("Bot id :  ")
        control_channel(id)
    else:
        try:
            bots.select(amount="all")
            r = eval(cmd,{"bots":bots})
            if r is not None:
                print(r)
        except Exception as e:
            print(e.__class__.__name__+": "+str(e))
        finally:pass
            

bots.selecteds_bots[0].result.start()
