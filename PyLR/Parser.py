__version__ = "$Id$"

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

    # the unspecified function (the default for all productions)
    def unspecified(*args):
        return args[1]

    def parse(self, text, verbose=0):
        """The parse algorithm for an LR-parser.
        Reference: [Aho,Seti,Ullmann: Compilerbau Teil 1, p. 266]
        """
	self.lexer.settext(text)
        # push the start state on the stack
        stack = [0]
	while 1:
	    tok, val = self.lexer.scan(verbose)
            state = stack[-1]
            action = self.actions[state][tok]
            if verbose:
                print "action",action
            if action[0]=='s':
                # push the symbol and the state
                stack = stack + [tok, action[1]]
            elif action[0]=='r':
                P = self.prodinfo[action[1]-1]
                # reduce P=A->b by popping 2*|b| from the stack
                stack = stack[:-2*P[0]]
                goto = self.gotos[stack[-1]][P[2]]
                # push A and the goto symbol
                stack = stack + [P[2], goto]
                if verbose:
		    print "reduce",P
                P[1](tok, val)
            elif action[0]=='a':
                return
            else:
                print "error"
                return

