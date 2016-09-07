# encoding: utf-8
import sys
sys.path.append("../..")
from chat.common import constant as conf
from chat.pyproto import base_pb2
from chat.pyproto import msgid_pb2
from chat.pyproto import service_pb2
from draw import Draw
from socketClient import DynaSocket
import time
import threading


class Client(object):
    def __init__(self):
        self.chart = None
        self.count = 0
        self.sock = DynaSocket()
        self.chart = None
        self.now = time.time()
        self.current_val = (0,0)
        self.work_thread = None

    def connect(self):
        self.work_thread = threading.Thread(target=self.sock.start,args=("120.27.240.62",conf.TEST_QUOTE_PORT,self.update))
        self.work_thread.start()

    def update(self,ttime,quote):
        self.current_val = (ttime,int(quote.Dynas))

    @property
    def Chart(self):
        if self.chart is None:
            return Draw("line",self.source)
        else:
            return self.chart

    @Chart.setter
    def Chart(self,shape):
        self.chart = Draw(shape,self.source)

    def source(self):
        #print "return %s" % str(self.current_val)
        return self.current_val


    '''
    /********************************************
     * 行情数据推送相关
     ************************************/
    '''
    def subon_ServiceDyna(self):
        msg = self.register_dyna(service_pb2.ServiceDyna,service_pb2.SubOn)
        self.sock.send(msg)

    def suboff_ServiceDyna(self):
        msg = self.register_dyna(service_pb2.ServiceDyna,service_pb2.SubOff)
        self.sock.send(msg)

    '''
        /**
         * 注册动态行情
         *
         */
    '''
    def register_dyna(self,service,subtype):
        req = service_pb2.Request()
        req.Service = service
        req.Sub = subtype

        baseMsg = base_pb2.BaseMsg()
        baseHead = base_pb2.BaseHead()
        baseBody = base_pb2.BaseBody()

        baseHead.ReqID = conf.dynasID
        baseHead.MsgID = msgid_pb2.Msg_Request
        baseBody.MsgData = req.SerializeToString()
        baseMsg.Head.CopyFrom(baseHead)
        baseMsg.Body.CopyFrom(baseBody)
        return baseMsg

if __name__ == "__main__":
    ct = Client()
    ct.connect()
    #ct.work_thread.join()
    #ct.subon_ServiceDyna()
    ct.Chart = "line"
    ct.Chart.Shape.paint()
