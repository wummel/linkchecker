import re, string, StringUtil

__version__ = "$Id$"

class Lexer:
    """This is a lexer class for PyLR.
    You add regular expressions with addpat(). The pattern added earlier
    also matches earlier.
    """

    def __init__(self):
        self.toklist = [("EOF", None, None)]
        self.lasttokindex = 0 # index of the first SKIP token minus one
        self.skiplist = []
        self.settext("")

    def settext(self, t):
        self.text = t
        self.rewind()

    def getTokenList(self):
        """return list of token names (leaving out the SKIP tokens)"""
        return map(lambda x: x[0], self.toklist[:(self.lasttokindex+1)])

    def rewind(self):
        self.textindex = 0

    def addpat(self, pat, tokname="", func=None, skip=0):
        """add search pattern to the lexer"""
        if tokname=="EOF":
            raise AttributeError, "EOF is a reserved token word"

        t = (tokname, re.compile(pat), func)
        if skip:
            self.toklist.append(t)
        else:
            self.lasttokindex = self.lasttokindex + 1
            self.toklist.insert(self.lasttokindex, t)
        self.irange = range(1,len(self.toklist))
	
    def __str__(self):
        return string.join(map(lambda x: str(x[0])+": "+str(x[1]), self.toklist), "\n")

    def scan(self, verbose=0):
	if self.textindex >= len(self.text):
            if verbose: print "tok=EOF(0), val=EOF"
	    return (0, "EOF")
	for i in self.irange:
            tok = self.toklist[i]
            mo = tok[1].match(self.text, self.textindex)
            if not mo: # avoid to match an empty string
                continue
            self.textindex = self.textindex + len(mo.group(0))
            if i > self.lasttokindex:
                return self.scan(verbose)
            else:
                if tok[2]:
                    val = apply(tok[2], (mo,))
                else:
                    val = mo.group(0)
                if verbose:
		    print "tok="+self.toklist[i][0]+"("+`i`+")"+", val="+`val`
                return (i, val)
        raise SyntaxError, "line "+\
            `StringUtil.getLineNumber(self.text, self.textindex)`+\
            ", near \""+self.text[self.textindex:self.textindex + 10]+"\""
