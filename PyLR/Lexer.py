import re, string, StringUtil

__version__ = "$Id$"

class PyLRSyntaxError(SyntaxError):
    pass

SKIPTOK = 0x01 # don't consider this a token that is to be considered a part of the grammar, like '\n'

class Lexer:
    """
    This is a lexer class for PyLR.

    Upon matching text, it must execute a function which will cause it
    to return a 2-tuple of type (tok, val) where token is an integer and
    val is just any python object that will later be passed as an argument
    to the functions that the parser will call when it reduces. For Example

    for the grammar

     E-> E + T
     E -> T
     T -> T * F
     T -> F
     F ->( E )
     F -> id

    it is likely that the lexer should return the token value of id <tok> and
    the integer value of id (string.atoi(id)).

    In addition, the lexer must always return (eof, something else) when it's done
    scanning to get the parser to continue to be called until parsing is done.
    """
    def __init__(self):
        self.toklist = [("EOF", None, None, 0)]
        self.settext("")

    def settext(self, t):
        self.text = t
        self.rewind()

    def getTokenList(self):
        """return list of token names"""
        return map(lambda x: x[0], self.toklist)

    def rewind(self):
        self.textindex = 0

    def addpat(self, pat, tokname=None, func=None, flags=0):
        """add search pattern to the lexer"""
        self.toklist.append((tokname, re.compile(pat), func, flags))
	
    def __str__(self):
        return string.join(map(lambda x: str(x[0])+": "+str(x[1]), self.toklist), "\n")

    def scan(self, verbose=0):
	if self.textindex >= len(self.text):
            if verbose: print "EOF"
	    return (0, "EOF")
	for i in range(1,len(self.toklist)):
            tok = self.toklist[i]
            mo = tok[1].match(self.text, self.textindex)
            if mo is None: # could be the empty string
                continue
            self.textindex = self.textindex + len(mo.group(0))
            if tok[3] & SKIPTOK:
                return self.scan(verbose)
            else:
                if tok[2]:
                    val = apply(tok[2], (mo,))
                else:
                    val = mo.group(0)
                if verbose: print str(i)+", "+str(val)
                return (i, val)
        raise PyLRSyntaxError, "line "+\
            `StringUtil.getLineNumber(self.text, self.textindex)`+\
            ", near \""+self.text[self.textindex:self.textindex + 10]+"\""
