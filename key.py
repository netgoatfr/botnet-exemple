import rsa
import os
import shortuuid as uuid
import logger
import time

def _content(file,mode="rb"):
    with open(file,mode=mode) as f:
        return f.read()

class PeerKeys:
    HARDNESS = 2048
    SEP = b"\n\n--\n--\n\n"
    MAX_TIME_HOUR = 12
    def __init__(self,peer_id):
        self.log = logger.Logger("PeerKey").get_instance(peer_id)
        self.id = peer_id
        self.file = f"peer-{self.id}.ftk"
        self.keypair = tuple()
        self.last_time = time.time()
        self.log.info("Loading keys from keys file...")
        if os.path.exists(self.file) and _content(self.file).strip() != b"":
            try:
                self._load(_content(self.file))
                self.log.info("Done.")
                if (time.time()-self.last_time) / 60 / 60 >= self.MAX_TIME_HOUR:
                    self.log.warning("The keys are too old!")
                    self.regenerate()
                return
            except Exception as e:
                self.log.critical("Error while loading the keys: "+e.__class__.__name__+": "+str(e))
                return
        self.log.info("Keys file not found or empty. Generating new keys.")
        self.keypair = rsa.newkeys(self.HARDNESS)
        self.log.info("Done. Writing keys to key file...")
        with open(self.file,mode="wb") as f:
            f.write(self._format())
        self.log.info("Done.")
    def _format(self):
        return str(time.time()).encode() + self.SEP + self.keypair[0].save_pkcs1() + self.SEP + self.keypair[1].save_pkcs1()
    def _load(self,datas):
        tmp = datas.split(self.SEP)
        self.keypair = (rsa.PublicKey.load_pkcs1(tmp[1]),rsa.PrivateKey.load_pkcs1(tmp[2]))
        self.last_time = float(tmp[0])
    def encrypt(self,data):
        if self.keypair:
            return rsa.encrypt(data,self.keypair[0])
    def decrypt(self,data):
        if self.keypair:
            return rsa.decrypt(data,self.keypair[1])
    def send_pub_key(self,sock):
        sock.send(self.keypair[0].save_pkcs1())
    def regenerate(self):
        self.log.info("Generating new keys...")
        self.keypair = rsa.newkeys(self.HARDNESS)
        with open(self.file,mode="wb") as f:
            f.write(self._format())
        self.log.info("Done.")
    def delete(self):
        self.log.info("Deleting key.")
        os.remove(self.file)
class ReceivedKey:
    def __init__(self,data):
        self.key = rsa.PublicKey.load_pkcs1(data)
    def encrypt(self,data):
        return rsa.encrypt(data,self.key)
    
def exec_time(func,*args,**kwargs):
    def wrapper():
        t1 = time.time()
        func(*args,**kwargs)
        t2 = time.time()
        print(f"Execution time for func {func.__name__} with args {args} and kwargs {kwargs} : {t2-t1}s")
    return wrapper

@exec_time
def main():
    global p
    p = PeerKeys("0111110")