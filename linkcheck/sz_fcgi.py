# -*- coding: iso-8859-1 -*-
# sz_fcgi.py - Multithreaded FastCGI Wrapper
__version__ 	= "v0.8  19/10/1998 ajung"
__doc__      	= "Multithreaded FastCGI Wrapper"

import thread
import linkcheck.fcgi


class SZ_FCGI (object):
    def __init__ (self, func):
        self.func = func

    # create a new thread to handle requests
    def run (self):
	try:
            while linkcheck.fcgi.isFCGI():
                req = linkcheck.fcgi.FCGI()
	        thread.start_new_thread(self.func,(self, req))
	except:
            import traceback
            traceback.print_exc(file=file('traceback', 'a'))
