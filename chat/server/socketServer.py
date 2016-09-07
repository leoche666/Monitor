# -*- coding=utf-8 -*-
import sys
sys.path.append("..")
import socket
import threading
from job import SocketJob,Jobs,Job
from chat.common import AESOperator
from chat.common import constant as conf
import struct
from chat.pyproto import base_pb2
from chat.pyproto import msgid_pb2
from chat.pyproto import service_pb2
import multiprocessing
import os
import time
#how many connections to allow
BACKLOG = 10
#size of int
SIZE_INT = 4
#sockect time out
SOCK_TIME_OUT = 30
#emitter interval
EMITTER_INTERVAL = 1
#max length of RESOURCE_POOL
MAX_RESOURCE_POOL = 1000
#receive all packages from rules and it will be sended in specified time
EMITTER_QUEUE = multiprocessing.Queue()
LOCK_RESOURCE_POOL = threading.Lock()

#this is a list that has many type of SocketPack
RULE_TYPE = ['SUM_RESQUEST','SUM_ERROE']

#this is the buffer area of the data recevied from the network process.
# Its size is limited by the MAX_RESOURCE_POOL field acquiescently
class ResPool(object):
   def __init__(self,max=MAX_RESOURCE_POOL):
       self.max = max
       self.pool = {}
       for ptype in RULE_TYPE:
           self.pool[ptype] = []

   def put(self,res):
       if len(self.pool[res.Ptype]) <= self.max:
           self.pool[res.Ptype].append(res)
       else:
           self.pool[res.Ptype] = [self.pool[res.Ptype][-1]]

   def get(self,ptype):
       try:
           return self.pool[ptype][-1]
       except IndexError:
           return None

RESOURCE_POOL = ResPool()

#all the collection data will be wraped this type which have two fields,the first is size of the data and
# the second is the content of the data
class SocketPack(object):
    def __init__(self,ptype,size,data):
        self.ptype = ptype
        self.size = size
        self.data = data

    @property
    def Ptype(self):
        return self.ptype

    @property
    def Size(self):
        return self.size

    @property
    def Data(self):
        return self.data

'''
ServerDyna object maintain the socket connection,and deal if receive package from the client
'''
class ServerDyna(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

'''
maintain the socket connect,and deal if receive package from the client
'''
def connection(sock,src_ip,src_port):
    #set the time out of the socket from the client
    sock.settimeout(SOCK_TIME_OUT)
    #build the base message to send
    baseMsg = base_pb2.BaseMsg()
    baseHead = None
    baseBody = None
    try:
        #recv size
        recv_num = struct.unpack('!i',sock.recv(SIZE_INT))[0]
        #recv data
        recvData = sock.recv(recv_num)
        recFmt = '%ds' % recv_num
        recv_msg = struct.unpack(recFmt,recvData)[0]

        #prase the data
        baseMsg.ParseFromString(recv_msg)
        baseHead = baseMsg.Head

        if baseHead.ReqID == conf.dynasID and baseHead.MsgID == msgid_pb2.Msg_Request:
            print "sub on dynasID"
            while True:
                with LOCK_RESOURCE_POOL:
                    #send size
                    size = RESOURCE_POOL.get('SUM_RESQUEST').Size
                    sock.send(size)
                    #send data
                    data = RESOURCE_POOL.get('SUM_RESQUEST').Data
                    sock.send(data)
                time.sleep(EMITTER_INTERVAL)
        else:
            pass
    except socket.timeout:
        print "%s time out" % str(sock)
    except Exception,ex:
        print "in connection " + str(ex)
    finally:
        sock.close()

'''
touch a thread for socket connection if have the request from the specified port
'''
def accept(sock_accept):
    print "This is Socket master process's child thread,now start accpet the port"
    while True:
        con,(src_ip,src_port) = sock_accept()
        print "receive a socket:%s,it's address is (%s,%d)" % (str(con),src_ip,src_port)
        threading.Thread(target=connection,args=(con,src_ip,src_port)).start()


'''
acquire the data if EMITTER_QUEUE have data,and put it into the specified list called RESOURCE_POOL if the length of the list is less
than MAX_RESOURCE_POOL
'''
def get_data():
    print "This is Socket master process's child thread,now start get the data"
    while True:
        data = EMITTER_QUEUE.get()
        with LOCK_RESOURCE_POOL:
            RESOURCE_POOL.put(data)

def start_SocketJob(instance,sock_accept):
    t = threading.Thread(target=instance,args=(sock_accept,))
    t.start()
    return t

def start_get_data(instance):
    t = threading.Thread(target=instance,args=())
    t.start()
    return t

'''
ServerClient deal all the socket connection which is listening the specified id and port.
It will create a socket job if socket connection reach and start the socket job immediately
'''
class ServerClient(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.jobs = Jobs()

    def bind(self,host=None,port=None):
        self.host,self.port = host,port
        assert host != None
        assert port != None
        assert type(port) == int
        #binding
        print "This is Socket master process bind address (%s,%d)" % (host,port)
        self.sock.bind((host,port))
        print "This is Socket master process listening,BACKLOG is %d" % (BACKLOG)
        self.sock.listen(BACKLOG)

    def __call__(self, *args, **kwargs):
        print "This is Socket master process and my pid is %d, my father process is %d,now working" %(os.getpid(), os.getppid())
        self.bind(*args)
        #start thread,all the sockets will send if get from the queue called EMITTER_QUEUE
        self.jobs.add_job(Job(get_data,start_get_data,))
        #start thread to accept the listen
        self.jobs.add_job(Job(accept,start_SocketJob,self.sock.accept,))
        #start and wait jobs
        [job() for job in self.jobs] and [job.wait("join",) for job in self.jobs]

    def __repr__(self):
        return "Server binding in %s address & %d port,now listening" % (self.host,self.port)



