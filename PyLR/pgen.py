#!/usr/bin/env python

import PyLR, PyLR.Grammar, sys, getopt
from PyLR.Parsers import GrammarParser

class ParserParser(GrammarParser):
    def __init__(self):
	GrammarParser.__init__(self)
	self.result = [] # to be populated with productions
	self.funcmap = {}
	self.usercode = ""
	self.lexdef = ""
	self.classname = "MyParser"
	self.idlist = []

    def idlistID(self, id):
	"idlist -> id"
	self.idlist.append(id)
	return [id]

    def singletolist(self, el):
	"rhslist -> rhs"
	return [el]

    def idl_idlistID(self, l, el):
	"idlist -> idlist id"
	self.idlist.append(id)
	l.append(el)
	return l

    def rhs_idlist(self, l):
	"rhs -> idlist"
	return l

    def rhseps(self):
	"rhseps -> "
	return []

    def rhs_idlist_func(self, l, lp, id, rp):
	"rhs -> idlist LPAREN ID RPAREN"
	self.funcmap[tuple(l)] = id
	return l

    def rhslist_OR_rhs(self, l, OR, el):
	"rhs -> rhslist OR rhs"
	l.append(el)
	return l

    def lhsdef(self, lhs, COLON, rhslist, SCOLON):
	"lhsdef -> ID COLON rhslist SCOLON"
	print lhs
	for rhs in rhslist:
	    self.result.append(PyLR.Grammar.Production(lhs, rhs))
	return None

    def lexdef(self, ld):
	self.lexdef = ld

    def addcode(self, code):
	self.usercode = self.usercode + "\n" + code

    def classname(self, name):
	self.classname = name

    def parse(self, text, outf, verbose=0):
	global g, toks, lexer
	PyLR.Parser.Parser.parse(self, text, verbose)
	# insert the functionnames
	for p in self.result:
	    funcname = self.funcmap.get(tuple(p.RHS), "unspecified")
	    p.setfuncname(funcname)
	#evaluate the lexer
	exec(self.usercode)
	lexer = eval(self.lexdef)

	# generate the tokens for grammar
	toks = lexer.getTokenList()
	# change the symbols to their numbers
	for p in self.result:
	    for si in range(len(p.RHS)):
		if p.RHS[si] in toks:
		    p.RHS[si] = toks.indexof(p.RHS[si])

	g = PyLR.Grammar.LALRGrammar(self.result, toks)
	print g
 	g.extrasource = self.usercode
 	print "done parsing, about to start parser generation (writing to %s)" % outf
 	if self.lexdef:
 	    g.writefile(outf, self.classname, self.lexdef)
 	else:
 	    g.writefile(outf, self.classname)
 	print "done"


def main():
    usage = "pgen.py infile outfile"
    args = sys.argv[1:]
    if len(args) != 2:
	print usage
	sys.exit(0)
    inf = args[0]
    outf = args[1]
    if inf == "-":
	f = sys.stdin
    else:
	f = open(inf)
    pspec = f.read()
#    f.close() # dont close stdin
    global pp # for use with python -i pgen.py <inf> <outf>
    pp = ParserParser()
    verbose=1
    pp.parse(pspec, outf, verbose)


if __name__ == "__main__":
    main()


