import re, PyLR

def _intfunc(m):
    return int(m.group(0))

class MathLex(PyLR.Lexer):
    def __init__(self):
	PyLR.Lexer.__init__(self)
	self.addpat(r"([1-9]([0-9]+)?)|0", "INT", _intfunc)
        self.addpat(r"\+", "PLUS")
        self.addpat(r"\*","TIMES")
        self.addpat(r"\(", "LPAR")
        self.addpat(r"\)", "RPAR")
	self.addpat(r"\s+", "WS", None, 1)
