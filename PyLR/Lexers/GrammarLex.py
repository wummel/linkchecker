"""
this file contains the Lexer that is used in parsing Grammar specifications
"""

import re,PyLR

def retlex(mo):
    return mo.group("lex")

def retcode(mo):
    return mo.group("code")

def retclass(mo):
    return mo.group("class")

class GrammarLex(PyLR.Lexer):
    def __init__(self):
	PyLR.Lexer.__init__(self)
	self.addpat(r"_lex\s+(?P<lex>[^\n]*)", "LEX", retlex)
	self.addpat(r"_code\s+(?P<code>[^\n]*)", "CODE", retcode)
	self.addpat(r"_class\s+(?P<class>[a-zA-Z_][a-zA-Z_0-9]*)", "CLASS", retclass)
        self.addpat(r"[a-zA-Z_][a-zA-Z_0-9]*", "ID")
        self.addpat(r":", "COLON")
        self.addpat(r";", "SCOLON")
        self.addpat(r"\|", "OR")
        self.addpat(r"\(", "LPAREN")
        self.addpat(r"\)", "RPAREN")
        self.addpat(r'"""', "GDEL")
	self.addpat(r"\s*#[^\n]*", "", None, 1)
	self.addpat(r"\s+", "", None, 1)

