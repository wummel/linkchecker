
__version__ = "$Id$"

import  PyLRengine


class Parser:

    def __init__(self, lexer, actiontable, gototable, prodinfo):
	self.lexer = lexer
	self.actions = actiontable
	self.gotos = gototable
        # get the function from the function name
        # if we forgot to supply a function we get an AttributeError here
        try: self.prodinfo = map(lambda x,s=self: (x[0], getattr(s, x[1]), x[2]),
	                         prodinfo)
        except AttributeError:
            sys.stderr.write("Parser: error: forgot to supply a parser function\n")
            raise
	self.engine = None

    # the unspecified function (the default for all productions)
    def unspecified(*args):
        return args[1]

    def initengine(self, dodel=0):
	self.engine = PyLRengine.NewEngine(self.prodinfo, self.actions, self.gotos)
	if dodel:
	    self.actions = []
	    self.gotos = []
	    self.prodinfo = []

    def parse(self, text, verbose=0):
	self.initengine()
	self.lexer.settext(text)
	while 1:
	    tok, val = self.lexer.scan(verbose)
	    if not self.engine.parse(tok, val, verbose):
		break
	# need to add a method to the engine to
	# return the final value
	# and return that here
	return None

    
