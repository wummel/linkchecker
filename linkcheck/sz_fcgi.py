# -*- coding: iso-8859-1 -*-
# sz_fcgi.py - Multithreaded FastCGI Wrapper
"""Multithreaded FastCGI Wrapper"""

import thread

import linkcheck.fcgi


class SzFcgi (object):
    """create threads to handle cgi requests"""

    def __init__ (self, func):
        """store function to execute on a request"""
        self.func = func

    def run (self):
        """create a new thread to handle requests"""
        try:
            while linkcheck.fcgi.isFCGI():
                req = linkcheck.fcgi.FCGI()
                thread.start_new_thread(self.func, (self, req))
        except:
            import traceback
            traceback.print_exc(file=file('traceback', 'a'))
