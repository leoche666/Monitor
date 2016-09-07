# encoding: utf-8
import struct
import dpkt
import threading
import os

class Rule(object):
    def __init__(self,**kwargs):
        self.set_rules(**kwargs)
        self.data = None

    @staticmethod
    def get_package(data):
        return dpkt.ethernet.Ethernet(data)

    def iptonet(self,ip_str):
        snippet=ip_str.split('.')
        return struct.pack("!i",int(snippet[0]) << 24 | int(snippet[1]) << 16 | int(snippet[2]) << 8 | int(snippet[3]))

    @property
    def IP_DST(self):
        return '%d.%d.%d.%d' % tuple(map(ord,list(self.rules['ip_dst'][0])))

    @property
    def IP_SRC(self):
        return '%d.%d.%d.%d' % tuple(map(ord,list(self.rules['ip_src'][0])))

    def set_rules(self,**kwargs):
        self.rules = kwargs
        if self.rules.has_key('ip_dst'):
            self.rules['ip_dst'] = (self.iptonet(kwargs['ip_dst']),
                                     lambda ip_data:ip_data if ip_data.dst == self.rules['ip_dst'][0] else False)

        if self.rules.has_key('ip_src'):
            self.rules['ip_src'] = (self.iptonet(kwargs['ip_src']),
                                     lambda ip_data:ip_data if ip_data.src == self.rules['ip_src'][0] else False)

        if self.rules.has_key('dport'):
            self.rules['dport'] = (kwargs['dport'],
                                    lambda ip_data:ip_data if ip_data.data.dport == self.rules['dport'][0] else False)

        if self.rules.has_key('http'):
            if kwargs['http'] == 'http.request':
                def is_http_request(ip_data):
                    if ip_data.data.dport == 80 and len(ip_data.data.data) > 0:
                        try:
                            self.data = dpkt.http.Request(ip_data.data.data)
                            return True
                        except Exception:
                            return False
                self.rules['http'] = ('http.request',is_http_request)
            elif kwargs['http'] == 'http.response':
                def is_http_response(ip_data):
                    if ip_data.data.dport == 80 and len(ip_data.data.data) > 0:
                        try:
                            self.data = dpkt.http.Response(ip_data.data.data)
                            return True
                        except Exception:
                            return False
                self.rules['http'] = ('http.response',is_http_response)

        self.rules_keys = self.rules.keys()

    def __str__(self):
        return str(self.rules)

    def __repr__(self):
        return str(self.rules)

    def __call__(self,queue):
        print "This is deal process and my pid is %d, my father process is %d,now working" %(os.getpid(), os.getppid())
        #add the thread to send message
        t = threading.Thread(target=self.send,args=())
        t.daemon = True
        t.start()

        while True:
            ip_data = queue.get()
            for myrules in self.rules_keys:
                if not self.rules[myrules][1](ip_data):
                    break
            else:
                if self.data is None:
                    self.data = ip_data.data
                self.analyze(self.data)

    #analyze the packages
    def analyze(self,data):
        pass

    #send the packages
    def send(self):
        pass