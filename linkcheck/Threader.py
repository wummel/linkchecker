from threading import *

class Threader:
    "A thread generating class"
    
    def __init__(self, num=5):
        self.maxThreads = num
        self.threads = []
    
    def acquire(self):
        "Wait until we are allowed to start a new thread"
        while 1:
            self.reduceThreads()
            if len(self.threads) < self.maxThreads:
                break

    def reduceThreads(self):
        for t in self.threads:
            if not t.isAlive():
                self.threads.remove(t)

    def finished(self):
        return not len(self.threads)

    def finish(self):
        self.reduceThreads()
        for t in self.threads:
            pass    # dont know how to stop a thread
        
    def startThread(self, callable, args):
        "Generate a new thread"
        self.acquire()
        t = Thread(None, callable, None, args)
        t.start()
        self.threads.append(t)
