import Lexer, re, string

def idfunc(m):
    return int(m.group(0))

class mathlex(Lexer.Lexer):
    def __init__(self):
	Lexer.Lexer.__init__(self)
	self.addpat(r"([1-9]([0-9]+)?)|0", "ID", idfunc)
        self.addpat(r"\+", "PLUS")
        self.addpat(r"\*","TIMES")
        self.addpat(r"\(", "LPAREN")
        self.addpat(r"\)", "RPAREN")
	self.addpat(r"\s+", "", None, Lexer.SKIPTOK)

