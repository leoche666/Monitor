# encoding: utf-8
import sys
sys.path.append("..")
from network import Control as cl
import chat.server.socketServer as ser
import multiprocessing
import threading
import struct
import time
from chat.pyproto import base_pb2
from chat.pyproto import service_pb2
from chat.pyproto import msgid_pb2
from chat.common import AESOperator
from chat.common import constant as conf
import os
from job import *
CLOCK = ser.EMITTER_INTERVAL
EMITTER_QUEUE = ser.EMITTER_QUEUE

#initize environment of the summary access amount of the merchant website
def init_access(cls):
    setattr(cls,"lock",threading.Lock())
    setattr(cls,"_analyze_access",0)
    setattr(cls,"analyze",analyze_access)
    setattr(cls,"send",send_access)

#add the summary access amount of the merchant website if have data
def analyze_access(cls,data):
     cls.lock.acquire()
     try:
        cls._analyze_access += 1
     finally:
         cls.lock.release()

#add the timing to reset the summary access of the merchant website before send message
def send_access(cls):
    while True:
        #base head
        baseHead = base_pb2.BaseHead()
        baseHead.ReqID = conf.dynasID
        baseHead.Time = int(time.time())
        baseHead.MsgID == msgid_pb2.Msg_Response

        #base body
        baseBody = base_pb2.BaseBody()
        response = service_pb2.Response()
        response.Result = service_pb2.ErrServiceOK
        response.Service = service_pb2.ServiceDyna
        response.Data.Obj = ""
        response.Data.Dynas = cls._analyze_access
        baseBody.MsgData = response.SerializeToString()

        #base msg
        baseMsg = base_pb2.BaseMsg()
        baseMsg.Head.CopyFrom(baseHead)
        baseMsg.Body.CopyFrom(baseBody)
        EMITTER_QUEUE.put(ser.SocketPack("SUM_RESQUEST",struct.pack('!i',baseMsg.ByteSize()),baseMsg.SerializeToString()))
        with cls.lock:
            cls._analyze_access = 0
        time.sleep(CLOCK)


class collection(object):
    def __init__(self):
        '''
        These jobs will be done,if you call start function of this instance
        '''
        self.jobs = Jobs()
        '''
        statistical term
        '''
        #summary access amount of the merchant website in the 'EMITTER_INTERVAL' interval
        self.sum_access = multiprocessing.Value('i', 0)
        self.lock = multiprocessing.Lock()

    @property
    def Network(self):
        return self.net

    def add_server(self,ip,port):
        '''
        listen specified port to receive the msg from the client,the msg will determine which server will be started
        '''
        def start_func(instance,ip,port):
            pro = multiprocessing.Process(target=instance,args=(ip,port,))
            pro.start()
            return pro

        server = ser.ServerClient()
        server.Daemon = True
        self.jobs.add_job(Job(server,start_func,ip,port))

    def add_pacay(self,dev):
        self.net = cl(dev)

    def add_filter(self,net,init,**rule):
        '''
        capture IP packages and filter by the idefined filtering.It can be idefined multiple
        '''
        if len(rule) == 0:
            raise ValueError("rule can't be empty,if you want to filter")

        from rule import Rule

        #init the Rule class
        init(Rule)
        #set the rule to filter the packages
        net.set_rule(Rule(**rule))


    def start_filter(self,net):
        def start_func(instance,):
            t = threading.Thread(target=instance,args=())
            t.start()
            return t

        job = Job(net,start_func,)
        self.jobs.add_job(job)

    def start(self):
        print "This is collection master process and my pid is %d, my father process is %d,now working" %(os.getpid(), os.getppid())
        #start and wait jobs
        [job() for job in self.jobs] and [job.wait("join",) for job in self.jobs]


if __name__ == '__main__':
    col = collection()
    #add the server to bind and listen for the specified port
    col.add_server("localhost",9999)
    #listen the dev
    col.add_pacay('en0')
    #collect summary access of the merchant website
    col.add_filter(col.Network,init_access,ip_dst='120.27.240.62',http='http.request',)
    col.start_filter(col.Network)
    #collect the real-time exceptional information of the merchanet website,which will be realized in the future
    #col.add_filter('en0',"line",ip_dst='120.27.240.62',http='http.request')
    #start the jobs for the collection moudle
    col.start()