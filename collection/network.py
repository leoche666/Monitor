# encoding: utf-8
# packet capture & decoding
import pcapy
import multiprocessing
import os
import threading
from rule import Rule
#core of cpu,if you just have please also set more than 2
CPU_CORE = 4
#size of ip package
MAX_SIZE_IP_PACKAGE = 65536


class Picking(object):
    def __init__(self,queue,dev):
        self.queue = queue
        self.dev = dev

    def __call__(self, *args, **kwargs):
        print "This is producer process and my pid is %d, my father process is %d,now working" %(os.getpid(), os.getppid())
        #TODO: sniffing the packages through the dev
        p = pcapy.open_live(self.dev, MAX_SIZE_IP_PACKAGE, False, 1)
        p.setfilter('tcp')
        p.loop(-1,self.padding)

    def padding(self,header,data):
        self.queue.put(data)


def handle_packet(working_queue,rules):
    #create a process for each rule,each process has one queue to aquire the data
    pool = []
    for rule in rules:
        que = multiprocessing.Queue()
        pool.append(que)
        p = multiprocessing.Process(target=rule, args=(que,))
        p.daemon = True
        p.start()

    print "This is customer process and my pid is %d, my father process is %d,now working" %(os.getpid(), os.getppid())
    while True:
        data = working_queue.get()
        p = Rule.get_package(data)
        #TODO filter the package
        [que.put(p.data) for que in pool]

class Control(object):
    def __init__(self,dev):
        self.rules = []
        self.working_queue = multiprocessing.Queue()
        self.dev = dev

    def set_rule(self,rule):
        self.rules.append(rule)

    def __call__(self, *args, **kwargs):
        #create a process deal the packet
        multiprocessing.Process(target=handle_packet, args=(self.working_queue,self.rules)).start()
        #capture the packet
        net = Picking(self.working_queue,self.dev)
        p = multiprocessing.Process(target=net, args=())
        p.start()
        #wait
        p.join()