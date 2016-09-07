# -*- coding=utf-8 -*-
import sys
sys.path.append("..")
import socket
import struct
from chat.common import constant as conf
from chat.common import AESOperator
from chat.pyproto import base_pb2
from chat.pyproto import msgid_pb2
from chat.pyproto import service_pb2

SOCK_TIME_OUT = 30


class StaticSocket(object):
    def __init__(self):pass

    def encrypt(self,baseMsg,key,iv):
        if len(baseMsg.Body.MsgData) > 0:
            baseMsg.Body.MsgData = AESOperator.AESOperator(key, iv).encrypt(baseMsg.Body.MsgData)

    def decrypt(self,baseMsg,key,iv):
        #decrypt the msgdata and token
        if len(baseMsg.Body.MsgData) > 0:
            baseMsg.Body.MsgData = AESOperator.AESOperator(key, iv).decrypt(baseMsg.Body.MsgData)

    def send(self,baseMsg,ip,port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip,port))
            #send size
            sock.send(struct.pack('!i',baseMsg.ByteSize()))
            #send data
            data = baseMsg.SerializeToString()
            fmt = '%ds' % len(data)
            sendData = struct.pack(fmt,data)
            sock.send(sendData)

            #prapare
            responseMsg  = base_pb2.BaseMsg()

            #recv size
            recv_num = struct.unpack('!i',sock.recv(4))[0]
            #recv
            recvData = sock.recv(recv_num)
            recFmt = '%ds' % recv_num
            recv_msg = struct.unpack(recFmt,recvData)[0]

            #result
            responseMsg.ParseFromString(recv_msg)
            return responseMsg
        except socket.error,msg:
            raise Exception(msg)
        finally:
            sock.close()

    def encrypt_send(self,baseMsg,ip,port,key,iv):
        #encrypt
        self.encrypt(baseMsg,key,iv)
        #send
        msg = self.send(baseMsg,ip,port)
        #decrypt
        self.decrypt(msg,key,iv)
        return msg

class DynaSocket(object):
    def __init__(self):
        pass

    def start(self,ip,port,call_back):
        self.quote_ip,self.quote_port = ip,port
        try:
            if not self.quote_ip or not self.quote_port:
                raise Exception("quote_ip or quote_port is empty")
            else:
                self.quote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.quote_sock.settimeout(SOCK_TIME_OUT)
                self.quote_sock.connect((self.quote_ip,self.quote_port))


            req = service_pb2.Request()
            req.Service = service_pb2.ServiceDyna
            req.Sub = service_pb2.SubOn

            baseMsg = base_pb2.BaseMsg()
            baseHead = base_pb2.BaseHead()
            baseBody = base_pb2.BaseBody()

            baseHead.ReqID = conf.dynasID
            baseHead.MsgID = msgid_pb2.Msg_Request
            baseBody.MsgData = req.SerializeToString()
            baseMsg.Head.CopyFrom(baseHead)
            baseMsg.Body.CopyFrom(baseBody)

            #send size
            self.quote_sock.send(struct.pack('!i',baseMsg.ByteSize()))
            #send data
            data = baseMsg.SerializeToString()
            fmt = '%ds' % len(data)
            sendData = struct.pack(fmt,data)
            self.quote_sock.send(sendData)

            #baseMsg = base_pb2.BaseMsg()
            while True:
                #recv size
                recvSize = self.quote_sock.recv(4)
                if len(recvSize) <=0:
                    #print "server close the socket"
                    continue
                else:
                    recv_num = struct.unpack('!i',recvSize)[0]
                #recv
                recvData = self.quote_sock.recv(recv_num)
                #result
                baseMsg.ParseFromString(recvData)

                reqId = baseMsg.Head.ReqID
                htime = baseMsg.Head.Time

                response = service_pb2.Response()
                response.ParseFromString(baseMsg.Body.MsgData)
                if reqId == conf.dynasID:
                     #行情列表动态行情数据
                    call_back(htime,response.Data)
                else:
                    pass
        except Exception:
            self.quote_sock.close()
            raise
