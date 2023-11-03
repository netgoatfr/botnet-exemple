import socket
import json
import os
import subprocess
import time
import subprocess
import os
import shortuuid


def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default


SEP = b"@"

class Socket:
    def to_json(self):
        return f'<Socket addr="{self.host}:{self.port}">'
    def __init__(self,host,port):
        self.host=host
        self.port =port
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        while 1:
            try:
                self.sock.connect((host,port))
                break
            except:
                time.sleep(30)
    def send(self,**kwargs):
        self.raw_send(json.dumps(kwargs).encode())
    def raw_send(self,data):
        print("TX: ",str(len(data)).encode()+SEP+data+SEP)
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
        print("RX: " + str(datas))
        return datas[:-1]


class Values(dict):
    def handle(self,data):
        if not data["action"].startswith("values_"):
            return
        a = data["action"][7:]
        if a == "set":
            self[data["key"]] = data["value"]
        elif a == "get":
            self["socket"].send(action="values_get_return",value=self.get(data["key"],None))
        elif a == "delete":
            self.pop(data["key"],default=None)
        elif a == "list":
            self["socket"].send(action="values_list_return",value=self)
    

class CmdBuffer:
    def __init__(self,command,*args,shell=False):
        self.cmd = [command,*args]
        self.proc = None
        self._shell = shell
        self.id = shortuuid.uuid()
    def start(self):
        self.proc = subprocess.Popen(self.cmd,shell = self._shell , stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
        os.set_blocking(self.proc.stdout.fileno(), False)
        os.set_blocking(self.proc.stderr.fileno(), False)
    @property
    def returncode(self):
        return self.proc.returncode
    @property
    def pid(self):
        return self.proc.pid
    
    @property
    def isalive(self):
        return self.proc.poll() is None
    def stop(self):
        self.proc.terminate()
    def kill(self):
        self.proc.kill()
    def write(self,data):
        self.proc.stdin.write(data)
    def read(self,length=None):
        return self.proc.stdout.read(length) or b''
    def read_err(self,length=None):
        return self.proc.stderr.read(length) or b''

class CmdManager:
    def to_json(self):
        s = {}
        for i,v in self.buffers.items():
            s[i] = {v.pid,v.returncode,v.isalive}
        return s
    def __init__(self):
        self.buffers = {}
    def new_command(self,cmd,*args,shell=False):
        """
        Start a new command.
        shell -> does the sent command automaticly start with /bin/sh for posix or cmd.exe for windows
        """
        buff = CmdBuffer(cmd,*args,shell)
        self.buffers[buff.id] = buff
        return buff.id
    def get(self,id):
        return self.buffers.get(id,None)
    def handle(self,data):
        a = data["action"]
        if not a.startswith("cmd_"):return
        a = a[4:]
        if a == "create":
            values["socket"].send(action="cmd_create_return",id=self.new_command(data["cmd"],data["args"],data["shell"]))
        elif a == "start":
            buff = self.get(data["id"])
            if buff:
                buff.start()
        elif a == "stop":
            buff = self.get(data["id"])
            if buff:
                buff.stop()
        elif a == "kill":
            buff = self.get(data["id"])
            if buff:
                buff.kill()
        elif a == "returncode":
            buff = self.get(data["id"])
            if buff:
                values["socket"].send(action="cmd_returncode_return",code=buff.returncode)
        elif a == "pid":
            buff = self.get(data["id"])
            if buff:
                values["socket"].send(action="cmd_pid_return",pid=buff.pid)
        elif a == "isalive":
            buff = self.get(data["id"])
            if buff:
                values["socket"].send(action="cmd_isalive_return",result=buff.isalive)
        elif a == "exists":
            buff = self.get(data["id"])
            values["socket"].send(action="cmd_exists_return",result= buff is not None)
        elif a == "write":
            buff = self.get(data["id"])
            if buff:
                buff.write(data["data"].encode() if data["data"] is str else data["data"])
        elif a == "read":
            buff = self.get(data["id"])
            if buff:
                values["socket"].send(action="cmd_read_return",result=buff.read(data["length"]))
        elif a == "read_err":
            buff = self.get(data["id"])
            if buff:
                values["socket"].send(action="cmd_read_err_return",result=buff.read_err(data["length"]))


values = Values()
values["cmd_manager"] = CmdManager()
values["socket"] = Socket("localhost",8000)
values["socket"].sock.setblocking(0)

while 1:
    try:
        data = values["socket"].recv()
    except KeyboardInterrupt:
        break
    except BlockingIOError:
        continue
    if not data or data["action"] == "exit":
        break
    values.handle(data)
    values["cmd_manager"].handle(data)
    
    if data["action"] == "ping":
        values["socket"].send(action="PONG")
values["socket"].sock.close()