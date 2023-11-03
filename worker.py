import socket
#import high_python.threads as thread
import json
import time
import logger
import channels
import random,string
import threading

class Bot:
    def __init__(self,sock,name,addr,group=None):
        self.name=name
        self.socket=sock
        self.channel = channels.Channel(self.socket,addr=addr,group=group,name=name)
        self.id=self.channel.id
        if group:
            self.group = group
            self.group.add_bot(self)
        else:
            self.group = None
    def __getattribute__(self,attr):
        if attr in object.__getattribute__(self,"__dict__"):
            return object.__getattribute__(self,"__dict__")[attr]
        return getattr(object.__getattribute__(self,"channel"),attr)


class BotGroup:
    def __init__(self,name):
        self.name=name
        self.logger = logger.Logger(name)
        self.actives_bots = {}
        self.bots = {}
        self.selecteds_bots = {}
        self.bots_details = {}
        self.muted = False
        self.debug = False
        self._ping_result = {}
        
    def _ping_a_bot(self,bot):
        self._ping_result[bot] = bot.ping()
    
    def mute(self):
        self.muted = True
        self.logger.info("Bot group Muted.")
    def demute(self):
        self.muted = False
        self.logger.info("Bot group Unmuted.")
        
    def add_bot(self,bot):
        if not self.muted:self.logger.info("added bot "+bot.name+f" ({bot.id})")
        self.bots[bot.id] = bot
        self.bots_details[bot.id] = {}
        return bot.id
    
    def remove_bot(self,id):
        if not self.muted:self.logger.info("removed bot "+self.bots[id].name+f" ({id})")
        del self.bots[id]
        

    def select(self,*,id=None,slice=None,amount=None):
        bots = []
        if id is not None:
            bots.extend([self.bots[id]])
        if slice is not None:
            bots.extend([self.bots[i] for i in list(self.bots.keys())[slice]])
        if amount is not None:
            bots.extend([self.bots[i] for i in list(self.bots.keys())[0:amount if amount != "all" else len(self.bots)]])
        self.selecteds_bots = bots
        if not self.muted:self.logger.info(f"{len(self.selecteds_bots)} bots are selected.")

    def deselect(self):
        self.selecteds_bots = []
        if not self.muted:self.logger.info(f"{len(self.selecteds_bots)} bots are now deselected.")

    
    def ping(self):
        if not self.muted:self.logger.info(f"Pinging {len(self.selecteds_bots)} selecteds bots ...")
        threads = []
        for i in self.selecteds_bots:
            threads.append(threading.Thread(target=self._ping_a_bot,args=(i,)))
        
        for i in threads:
            i.start()
            i.join()
        
        times = {}
        for bot,v in self._ping_result.items():
            times[bot.id] = v
            if v == -1:
                self.logger.warning(f"Connection lost with Bot-{bot.id} ({bot.name})")
                self.selecteds_bots.remove(bot)
                if self.debug:
                    self.logger.debug(f"Bot-{bot.id} ({bot.name}) de-selected.")
            elif v == -2:
                self.logger.warning(f"Unable to retreive a response with Bot-{bot.id} ({bot.name}). It may not have a good connection.")
                self.selecteds_bots.remove(bot)
                if self.debug:
                    self.logger.debug(f"Bot-{bot.id} ({bot.name}) de-selected.")
            else:
                self.bots_details[bot.id]["last_ping_time"] = v
                
        if not self.muted:self.logger.info(f"{len(self.selecteds_bots)} bots where pinged.")    
    def execute(self,command,*args,**kwargs):
        if not self.muted:self.logger.info(f"Atteming to execute \"{command}\" ...")
        not_respond = []
        for i in self.selecteds_bots:
            buffer = i.execute(command,*args)
            if not buffer.id:
                not_respond.append(i)
            if self.debug:
                if buffer.id:
                    if not self.muted:self.logger.info(f"Command executed for Bot-{bot.id} ({bot.name})")
                else:
                    self.logger.warning(f"Bot-{bot.id} ({bot.name}) didn't respond.")
            self.bots_details[i.id]["last_command_buffer"] = buffer
            self.bots_details[i.id]["last_command_executed"] = command + str(args)
            
        if not self.muted:self.logger.info(f"Command executed on {len(self.selecteds_bots)} bots, and {len(not_respond)} bots didn't responded.")

    def control(self,cmd):
        if not self.muted:self.logger.info(f"Atteming to control {len(self.selecteds_bots)} selecteds bots ...")
        for i in self.selecteds_bots:
            try:
                i.result = eval(cmd,{"bot":i})
                if i.result:
                    print(f"Bot-{i.id} ({i.name}): "+str(i.result))
            #except Exception as e:
            #    print(f"Bot-{i.id} ({i.name}): ",e.__class__.__name__,":",e)
            finally:
                pass
    def details(self):
        self.logger.info(f"Here is the details for {len(self.selecteds_bots)} selecteds bots:")
        for i,v in self.bots_details.items():
            print("Bot-"+str(i)+":")
            for i,v in v.items():
                print("\t"+i.replace("_"," ").capitalize()+" :   "+str(v))
                
    def stop(self):
        for bot in self.selecteds_bots:
            bot.stop()
            del self.actives_bots[bot.id]
        self.logger.info(f"Stopped {len(self.selecteds_bots)} bots.")

    def mute_bots(self):
        for bot in self.selecteds_bots:
            bot.mute()
        if not self.muted:self.logger.info(f"Mutted {len(self.selecteds_bots)} bots.")
            
    def unmute_bots(self):
        for bot in self.selecteds_bots:
            bot.unmute()
        if not self.muted:self.logger.info(f"Demuted {len(self.selecteds_bots)} bots.")

    def active(self):
        return {"total":len(self.bots),"running":len(self.actives_bots),"remaining":len(self.bots)-len(self.actives_bots),"selecteds":len(self.selecteds_bots)}

if __name__ == "__main__":
    bg = BotGroup("Botgroup")
    for _ in range(30):
        _ = Bot(socket.socket(),"".join(random.choices(string.ascii_lowercase,k=5)),("localhost,",8000),bg)