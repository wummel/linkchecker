# sz_fcgi.py - Multithreaded FastCGI Wrapper
__version__ 	= "v0.8  19/10/1998 ajung"
__doc__      	= "Multithreaded FastCGI Wrapper"


import sys,thread,fcgi

class SZ_FCGI:

	# Constructor
	def __init__(self,func):
		self.func = func
		self.handles  = {}
		return None

	# create a new thread to handle requests
	def run(self):
		try:
			while fcgi.isFCGI():
				req = fcgi.FCGI()
				thread.start_new_thread(self.handle_request,(req,0))

		except:
			write_log('isCGI() failed')


	# Finish thread and send all data back to the FCGI parent
	def finish(self):
		req  = self.handles[thread.get_ident()]
		req.Finish()
		thread.exit()	
		


	# Call function - handled by a thread
	def handle_request(self,*args):

		req = args[0]
		self.handles[thread.get_ident()] = req

		try:
			self.func(self,req.env,req.getFieldStorage())
		except:
			pass


	# Our own FCGI print routine
	def pr(self,*args):
	
		req = self.handles[thread.get_ident()]

		try:
			s=''
			for i in args: s=s+str(i)
			req.out.write(s+'\n')
			req.out.flush()
		except:
			pass


