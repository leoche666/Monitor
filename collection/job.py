# encoding: utf-8
SOCK_TIME_OUT = 30

'''
multiple jobs will defined in the module,you can pick one kind of job to do your work.
'''
class Job(object):
    def __init__(self,instance,start_func,*args):
        self.instance = instance
        self.start_func = start_func
        self.args = args
        self.major = None

    def __call__(self):
        self.major = self.start_func(self.instance,*self.args)
        return self

    def wait(self,wait_func,*args):
        if hasattr(self.major,wait_func):
            eval("self.major."+wait_func+str(args))
        else:
            raise TypeError(str(self.major.__class__) + " hasn't %s method" % wait_func)

    def __repr__(self):
        return str(self.instance)

'''
Jobs is an iterator,has some jobs to do
'''
class Jobs(object):
    def __init__(self):
        self.group = []
        self.crt_index = 0

    def add_job(self,job):
        self.group.append(job)

    def __iter__(self):
        self.crt_index = 0
        return self

    def next(self):
        if self.crt_index < len(self.group):
            self.crt_index += 1
            return self.group[self.crt_index - 1]
        else:
            raise StopIteration

'''
Socket connection can be see the SocketJob,this class just provide some base function.if you have the another things to do,
Please inherit and extend it.
'''
class SocketJob(Job):
    def __init__(self,con_adr,start_func,*args):
        self.con,(self.src_ip,self.src_port) = con_adr
        self.con.settimeout(SOCK_TIME_OUT)
        Job.__init__(self,con_adr,start_func,*args)

    def kill_self(self):
        pass

