# -*- coding: iso-8859-1 -*-
# sz_fcgi.py - Multithreaded FastCGI Wrapper
__version__ 	= "v0.8  19/10/1998 ajung"
__doc__      	= "Multithreaded FastCGI Wrapper"


import thread,fcgi

class SZ_FCGI:
    def __init__(self,func):
        self.func = func

    # create a new thread to handle requests
    def run(self):
	try:
            while fcgi.isFCGI():
                req = fcgi.FCGI()
	        thread.start_new_thread(self.func,(self, req))
	except:
            import traceback
            traceback.print_exc(file = open('traceback', 'a'))
