"""Threading support"""
# Copyright (C) 2000,2001  Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

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
        # dont know how to stop a thread
        
    def startThread(self, callable, args):
        "Generate a new thread"
        self.acquire()
        t = Thread(None, callable, None, args)
        t.start()
        self.threads.append(t)
