__version__ = "$Id$"

import sys,time,string,types,parsertemplate,Lexer,Set

class ParseError(SyntaxError):
    pass

class Production:
    """Production -- a Grammar is really just a list of productions.
    The expected structure is a symbol for the lhs and a list of
    symbols or symbols for the rhs."""
    def __init__(self, lhs, rhs, funcname="unspecified"):
	self.lhs = lhs
	self.rhs = rhs
	self.funcname = funcname
	self.func = None # will be assigned dynamically
        self.toklist = None

    def __len__(self):
	return len(self.rhs)

    def __repr__(self):
        return self.getrep()

    def getrep(self, toklist=None):
	s = self.lhs+":"
        for t in self.rhs:
            if type(t)==types.IntType and toklist:
                s = s+" "+toklist[t]
            else:
                s = s+" "+str(t)
        return s+" ("+self.funcname+")"

    def items(self):
	return range(len(self.rhs) + 1)


class Grammar:
    """Provides methods for producing the actiontable, the gototable, and the
    prodinfo table.  Using these functions, it can produce a python source
    code file with these tables.
    Note that we assume the first production (productions[0]) to be the start
    symbol."""

    EPS = -1
    DummyLA = -2

    def __init__(self, productions, tokens, verbose=0):
        if not (productions or tokens):
            raise ParseError, "empty production or token list"
	self.verbose = verbose
	self.productions = productions
        self.tokens = tokens
	self.terminals = range(len(tokens))
	self.nonterminals = map(lambda p: p.lhs, self.productions)
        for p in self.productions:
            for s in p.rhs:
                if (s not in self.terminals) and (s not in self.nonterminals):
                    raise ParseError, "invalid symbol "+`s`+\
		    " in production '"+`p`+"'"
        if self.verbose:
            print "Terminals:", self.terminals
            print "Nonterminals:", self.nonterminals
        self._reduceGrammar()
        # build map with productions who have the same lhs
	self.lhsprods = {}
	for lhs in self.nonterminals:
	    self.lhsprods[lhs] = filter(lambda x,l=lhs: x.lhs==l,
	                                self.productions)
	self._genDerivedEpsilons()
	self._genFIRSTmap()
        self._genFOLLOWmap()
	self.LALRitems = []
	# help make epsilon productions work with kernel items
	# and to compute goto transitions from kernel
	self._genNTFIRSTmap()
	# help make shifts work with only kernel items
	self._genTFIRSTmap()

    def _reduceGrammar(self):
        """Definitions:
	(1) not productive
	    a nonterminal A is not productive iff there is no
            word u with A ==>* u
            This means A produces no words in the grammar.
        (2) not reachable
            a nonterminal A is no reachable iff there are no words
            a,b with S ==>* aAb
            This means A occurs never in a parsetree if we derive a word.

        This function eliminates all nonterminals which are not productive
        or not reachable.
        If we reduce the start symbol, the grammar produces nothing and
        a ParseException is thrown.

        References: [R. Wilhelm, D.Maurer: "Ubersetzerbau, p. 300f]
        """
        # productive nonterminals
        productive_nts = []
        # rest_nt[p] == the number of nonterminals in p.rhs which are not yet
        # marked as productive
        # if rest_nt[p]==0 then p is productive
        rest_nt = {}
        # if we find a productive nonterminal A, we have to inspect all
        # other nonterminals with A. this is the reason we add all found
        # productive nts to this list
        workedon_nts = []
        # mark terminals as productive (even epsilon-productions)
        for p in self.productions:
            rest_nt[p]= len(filter(lambda x, s=self: x in s.nonterminals, p.rhs))
            if rest_nt[p]==0:
                productive_nts.append(p.lhs)
                workedon_nts.append(p.lhs)
        # work on the productive list
        while workedon_nts:
            x = workedon_nts[0]
            # search for production p with x in p.rhs
            for p in filter(lambda p, _x=x: _x in p.rhs, self.productions):
                rest_nt[p] = rest_nt[p] - 1
                if not p.lhs in productive_nts:
                    productive_nts.append(p.lhs)
                    workedon_nts.append(p.lhs)
            workedon_nts.remove(x)
        if not self.productions[0].lhs in productive_nts:
            raise ParseError, "start symbol of grammar is not productive"

        # reachable nonterminals
        reachable_nts = [self.productions[0].lhs] # start symbol is reachable
        added=1
        while added:
            added = 0
            for p in self.productions:
                for r in p.rhs:
                    if p.lhs in reachable_nts and (r in self.nonterminals and
		    r not in reachable_nts):
                        reachable_nts.append(r)
                        added = 1

        # reduce the grammar
        self.productions = filter(lambda p, pnt=productive_nts,
                  rnt=reachable_nts: (p.lhs in pnt) and (p.lhs in rnt),
                  self.productions)
        if self.verbose:
            print "Reduced grammar:\n"+`self`

    def __repr__(self):
        """I like functional programming :)"""
	return string.join(map(lambda x,s=self: x.getrep(s.tokens),
	                       self.productions),";\n")+";"

    def _genDerivedEpsilons(self):
	"""determines the nonterminals that can derive epsilon"""
	res = {}
	for p in self.productions:
	    if not p.rhs:
		res[p.lhs] = 1
        self.lhseps = res.keys()
        added=1
        while added:
            added=0
            for p in self.productions:
                if filter(lambda x,r=res: not r.has_key(x), p.rhs) and \
		   not res.has_key(p.lhs):
                    res[p.lhs]=added=1
        self.lhsdereps = res.keys()


    def _genFIRSTmap(self):
	"""return dictionary d with d[A] = FIRST(A) for all symbols A
	"""
	self.firstmap = {}
	for sym in [Grammar.EPS, Grammar.DummyLA]+self.terminals:
	    self.firstmap[sym] = {sym: 1}
        added=1
	while added:
	    added = 0
	    for nt in self.nonterminals:
		firsts = self.firstmap.get(nt, {})
		for p in self.lhsprods[nt]:
		    if not p.rhs:
			if not firsts.has_key(Grammar.EPS):
			    added = firsts[Grammar.EPS] = 1
		    for Y in p.rhs:
			f = self.firstmap.get(Y, {})
			for a in f.keys():
			    if not firsts.has_key(a):
				added = firsts[a] = 1
			if not Y in self.lhsdereps:
			    break
		self.firstmap[nt] = firsts
	for s in self.firstmap.keys():
	    self.firstmap[s] = self.firstmap[s].keys()


    def FIRST(self, gs_list):
        """extend FIRST to set of symbols
	precondition: we already have calculated FIRST for all single
	symbols and stored the values in self.firstmap
        """
        assert gs_list, "list must be nonempty"
	res = {}
        allhaveeps=1
	for X in gs_list:
            set = self.firstmap[X]
	    for s in set:
                res[s] = 1
            if not Grammar.EPS in set:
                allhaveeps=0
                break
	if allhaveeps:        
	    res[Grammar.EPS] = 1
	return res.keys()

    def _augment(self):
	"""this function adds a production S' -> S to the grammar where S was
	the start symbol.
	"""
	newsym = self.productions[0].lhs+"'"
	while newsym in self.nonterminals:
	    newsym = newsym+"'"
	self.productions.insert(0, Production(newsym, 
					      [self.productions[0].lhs]))
        self.lhsprods[newsym] = self.productions[0]

    def _genFOLLOWmap(self):
        """dictionary d with d[A] = FOLLOW(A) for all nonterminals A
        """
	self.FOLLOWmap = {}
        for nt in self.nonterminals+self.terminals:
	    self.FOLLOWmap[nt] = []
	self.FOLLOWmap[self.productions[0].lhs] = [0] # 0 is EOF token
        added=1
        while added:
            added=0
            for p in self.productions:
                for i in range(1,len(p.rhs)):
                    B = p.rhs[i-1]
                    beta = p.rhs[i]
                    for f in self.firstmap[beta]:
                        if f != Grammar.EPS and f not in self.FOLLOWmap[B]:
                            self.FOLLOWmap[B].append(f)
                            added=1
            for p in self.productions:
                for i in range(len(p.rhs)):
                    B = p.rhs[i]
                    dereps=1
                    for X in p.rhs[(i+1):]:
                        if X in self.terminals or (X not in self.lhsdereps):
                            dereps=0
                    if dereps:
		        for f in self.FOLLOWmap[p.lhs]:
                            if f not in self.FOLLOWmap[B]:
                                self.FOLLOWmap[B].append(f)
                                added=1

    def _closure(self, items):
        """Reference: [Aho,Seti,Ullmann: Compilerbau Teil 1, p. 282]
        """
        res = {}
        for item in items.keys():
            res[item]=0
        more = 1
	while more:
            more = []
	    for prodind, rhsind, term in res.keys():
                prod = self.productions[prodind]
		if rhsind >= len(prod.rhs):
		    continue
		for p in self.lhsprods.get(prod.rhs[rhsind], []):
		    try:
			newpart = prod.rhs[rhsind + 1]
		    except IndexError:
			newpart = Grammar.EPS
		    for t in self.FIRST([newpart, term]):
                        item = (self.productions.index(p), 0, t)
			if not res.has_key(item):
			    more.append(item)
#                    if term == 0 and newpart == Grammar.EPS:
#                        item = (self.productions.index(p), 0, 0)
#                        if not res.has_key(item):
#                            more.append(item)
	    for item in more:
		res[item]=0
	return res

    def prodinfotable(self):
	"""returns a list of three pieces of info for each production.
	The first is the lenght of the production, the second is the
	function name associated with the production and the third is
	is the index of the lhs in a list of nonterminals.
	"""
	return map(lambda p,s=self: (len(p.rhs),
	           p.funcname, s.nonterminals.index(p.lhs)), self.productions)

    def _genNTFIRSTmap(self):
	"""computes all nonterms A, first of (strings n) such that some
	nonterminal B derives [A, n] in zero or more steps of rightmost
	derivation. used to help make epsilon productions quickly calculable.
	(B may == A)
	"""
	self.ntfirstmap = {}
        for p in self.nonterminals:
            self.ntfirstmap[p] = {}
	for p in self.productions:
	    if p.rhs and p.rhs[0] in self.nonterminals:
		self.ntfirstmap[p.lhs][p.rhs[0]] = 0
        foundmore = 1
	while foundmore:
	    foundmore = 0
	    reskeys = self.ntfirstmap.keys()
	    for nt in reskeys:
		rhsdict = self.ntfirstmap[nt]
		for rnt in rhsdict.keys():
		    if rnt in reskeys:
			d = self.ntfirstmap[rnt]
			for k in d.keys():
			    if not self.ntfirstmap[nt].has_key(k):
				foundmore = 1
 				self.ntfirstmap[nt][k] = 0
	# this part accounts for the fact that a nonterminal will
	# produce exactly itself in zero steps
	for p in self.productions:
            self.ntfirstmap[p.lhs][p.lhs] = 0
	
    def _genTFIRSTmap(self):
	"""for each nonterminal C, compute the set of all terminals a, such
	that C derives ax in zero or more steps of (rightmost) derivation
	where the last derivation is not an epsilon (empty) production.
	
	assumes .mkfirstntmap() has been run and has already produced
	self.ntfirstmap
	"""
	self.tfirstmap = {}
        for nt in self.nonterminals:
            self.tfirstmap[nt] = []
	for p in self.productions:
	    if p.rhs and p.rhs[0] in self.terminals:
		self.tfirstmap[p.lhs].append(p.rhs[0])
        foundmore = 1
	while foundmore:
	    foundmore = 0
	    reskeys = self.tfirstmap.keys()
	    for nt in self.ntfirstmap.keys():
		arrows = self.ntfirstmap[nt]
		for k in arrows.keys():
		    for t in self.tfirstmap[k]:
			if t not in self.tfirstmap[nt]:
			    foundmore = 1
			    self.tfirstmap[nt].append(t)

    def _goto(self, itemset, sym):
        """reference: [Aho,Seti,Ullmann: Compilerbau Teil 1, p. 293]"""
	res = []
	for pi, ri in itemset:
	    if ri == len(self.productions[pi].rhs):
		continue
	    s = self.productions[pi].rhs[ri]
	    if s == sym:
		res.append((pi, ri+1))
            d = self.ntfirstmap.get(s, {})
	    for k in d.keys():
		for p in self.lhsprods[k]:
		    if p.rhs and p.rhs[0] == sym:
			i = self.productions.index(p)
			if (i, 1) not in res: res.append((i, 1))
	res.sort()
	return res

    def _lookaheads(self, itemset):
	spontaneous = []
	propagates = {}
	gotomap = {}
	for kpi, kri in itemset:
            propagates[(kpi,kri)] = []
	    C = self._closure({(kpi, kri, Grammar.DummyLA):0})
	    for cpi, cri, t in C.keys():
		if cri == len(self.productions[cpi].rhs):
		    continue
		X = self.productions[cpi].rhs[cri]
		if gotomap.has_key(X):
		    newstate = gotomap[X]
		else:
		    gotomap[X] = newstate = self.kernelitems.index(\
		        self._goto(itemset, X))
		if t != Grammar.DummyLA:
		    spontaneous.append((newstate, (cpi, cri+1), t))
		else:
                    propagates[(kpi, kri)].append((newstate, (cpi, cri+1)))
	return spontaneous, propagates

    def _genKernelitems(self):
	self.kernelitems = todo = [[(0, 0)]]
        newtodo = 1
	while newtodo:
	    newtodo = []
	    for items in todo:
		for s in self.nonterminals + self.terminals:
		    g = self._goto(items, s)
		    if g and g not in self.kernelitems:
			newtodo.append(g)
            if self.verbose:
	        print "found %d more kernels" % (len(newtodo))
            self.kernelitems = self.kernelitems + newtodo
            todo = newtodo
        if self.verbose:
            print "generated kernelitems:",self.kernelitems

    def _initLALR1items(self):
	self._genKernelitems()
	if self.verbose:
	    print "initializing lookahead table..."
	props = {}
	la_table = []
	for itemset in self.kernelitems:
	    la_table.append([])
	    for item in itemset:
		la_table[-1].append([])
	la_table[0][0].append(0) # EOF
	for i in range(len(self.kernelitems)):
            sp, pr = self._lookaheads(self.kernelitems[i])
	    for ns, item, t in sp:
                inner = self.kernelitems[ns].index(item)
                if t not in la_table[ns][inner]:
                    la_table[ns][inner].append(t)
	    props[i] = pr
        if self.verbose:
            print "Lookahead table:",la_table
            print "Propagations:",props
	return la_table, props

    def _genLALR1items(self):
	la_table, props = self._initLALR1items()
	if self.verbose:
	    print "calculating lookahead table..."
        added_la=1
	while added_la:
	    added_la = 0
	    state_i = 0
	    for state in la_table:
		ii = 0
		for propterms in state:
		    if not propterms:
			ii = ii + 1
			continue
		    item = self.kernelitems[state_i][ii]
		    ii = ii + 1
		    try:
			proplist = props[state_i][item]
		    except KeyError:
			continue
		    for pstate, pitem in proplist:
			inner = self.kernelitems[pstate].index(pitem)
			for pt in propterms:
			    if pt not in la_table[pstate][inner]:
				added_la = 1
				la_table[pstate][inner].append(pt)
		state_i = state_i + 1

        if self.verbose:
            print "Lookahead table:",la_table
	# this section just reorganizes the above data
	# to the state it's used in later...
	if self.verbose:
	    print "reorganizing the data..."
	self.LALRitems = []
	state_i = 0
	for state in self.kernelitems:
	    item_i = 0
	    inner = []
	    for item in state:
 		for term in la_table[state_i][item_i]:
 		    if (item, term) not in inner:
 			inner.append((item, term))
		item_i = item_i + 1
	    inner.sort()
	    self.LALRitems.append(inner)
	    state_i = state_i + 1
        if self.verbose:
            print "LALR items:",self.LALRitems

    def actiontable(self):
	res = []
	state_i = 0
        terms = self.terminals[:]
        terms.append(Grammar.EPS)
	
	errentry = ("", -1)
	for state in self.LALRitems:
	    res.append([errentry] * len(terms))
	    for (prodind, rhsind), term in state:
		if rhsind == len(self.productions[prodind].rhs):
		    if prodind != 0:
			new = ("r", prodind)
			old = res[state_i][terms.index(term)]
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i,
			    terms.index(term)), old, "->", new
			res[state_i][terms.index(term)] = new
		    else:
			new = ("a", -1)
			old = res[state_i][terms.index(term)]
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i,
			    terms.index(term)), old, "->", new
			res[state_i][terms.index(term)] = new

		# calculate reduction by epsilon productions 
		elif self.productions[prodind].rhs[rhsind] in self.nonterminals:
		    nt = self.productions[prodind].rhs[rhsind]
		    ntfirst = self.firstmap[nt]
		    ntfirsts = self.ntfirstmap.get(nt, {})
		    for k in ntfirsts.keys():
			if k in self.lhseps:
			    reduceterms = self.followmap[k]
			    print `((prodind, rhsind), term)`, reduceterms
			    for r in reduceterms:
   				inner = terms.index(r)
   				old = res[state_i][inner]
   				new = ("r", self.lhseps[k])
  			        if old != errentry and old != new:
  				    print "Conflict[%d,%d]:" % (state_i,
				    inner), old, "->", new
  				res[state_i][inner] = new

		    # calculate the shifts that occur but whose normal items aren't in the kernel
		    tfirsts = self.tfirstmap[nt]
		    for t in tfirsts:
			inner = terms.index(t)
			g = self._goto(self.kernelitems[state_i], t)
			old = res[state_i][inner]
			try:
			    news = self.kernelitems.index(g)
			except ValueError:
			    continue
			new = ("s", news)
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i,
			    inner), old, "->", new
			res[state_i][inner] = new

		# compute the rest of the shifts that occur 'normally' in the kernel
		else:
		    t = self.productions[prodind].rhs[rhsind]
		    inner = terms.index(t)
		    gt = self._goto(self.kernelitems[state_i], t)
		    if gt in self.kernelitems:
			news = self.kernelitems.index(gt)
			old = res[state_i][inner]
			new = ("s", news)
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i,
			    inner), old, "->", new
			res[state_i][inner] = new
	    state_i = state_i + 1
	return res

    def gototable(self):
	items = self.kernelitems
	res = []
	state_i = 0
	nonterms = self.nonterminals
	err = None
	for state in items:
	    res.append([err] * len(nonterms))
	    nonterm_i = 0
	    for nt in nonterms:
		goto = self._goto(state, nt)
		if goto in items:
		    res[state_i][nonterm_i] = items.index(goto)
		nonterm_i = nonterm_i + 1
	    state_i = state_i + 1
	return res

    def writefile(self, filename, parsername="MyParser", lexerinit = "PyLR.Lexer.Lexer()"):
        self._augment()
        self._genLALR1items()
	at = self.actiontable()
	gt = self.gototable()
        self.productions = self.productions[1:]
	pi = self.prodinfotable()
	template = parsertemplate.__doc__
	vals = {"parsername": parsername, "lexerinit": lexerinit}
	vals["date"] = time.ctime(time.time())
	vals["filename"] = filename
	if not hasattr(self, "extrasource"):
	    vals["extrasource"] = ""
	else:
	    vals["extrasource"] = self.extrasource
	vals["grammar"] = `self`
	actiontable_s = "[\n\t"
	for l in at:
	    actiontable_s = "%s%s,\n\t" % (actiontable_s, `l`)
	vals["actiontable"] = actiontable_s[:-3] + "\n]\n\n"
	gototable_s = "[\n\t"
	for l in gt:
	    gototable_s = "%s%s,\n\t" % (gototable_s, `l`)
	vals["gototable"] = gototable_s[:-3] + "\n]\n\n"
	pi_s = "[\n\t"
	pii = 0
	vals["symbols"] = `self.tokens`
	prod2func_s = "Production" + " " * 45 + "Method Name\n" 
	for l, f, e in pi:
	    pi_s = "%s(%d, '%s', %d),%s# %s\n\t" % (pi_s, 
						    l, 
						    self.productions[pii].funcname, 
						    e, 
						    " " * (18 - len(self.productions[pii].funcname)),
						    `self.productions[pii]` )
	    pii = pii + 1
	vals["prodinfo"] = pi_s + "]\n\n"
	fp = open(filename, "w")
	fp.write(template % vals)
	fp.close()


def _makeprod(x):
    if len(x)==3: return Production(x[0],x[1],x[2])
    if len(x)==2: return Production(x[0],x[1])
    raise AttributeError, "Invalid Production initializer"

def _bootstrap():
    # dang, how did scott bootstrap the GrammarParser??
    # have to make this by hand
    import Lexers

    # define the productions
    toks = Lexers.GrammarLex().getTokenList()
    prods = map(_makeprod,
        [("pspec", ["gspec"]),
         ("pspec", ["pydefs", "gspec"]),
	 ("gspec", [toks.index("GDEL"), "lhsdeflist", toks.index("GDEL")]),
	 ("pydefs", ["pydefs", "pydef"]),
	 ("pydefs", ["pydef"]),
	 ("pydef", [toks.index("LEX")], "lexdef"),
	 ("pydef", [toks.index("CODE")], "addcode"),
	 ("pydef", [toks.index("CLASS")], "classname"),
	 ("lhsdeflist", ["lhsdeflist", "lhsdef"]),
	 ("lhsdeflist", ["lhsdef"]),
	 ("lhsdef", [toks.index("ID"), toks.index("COLON"), "rhslist", toks.index("SCOLON")], "lhsdef"),
	 ("rhslist", ["rhs"], "singletolist"),
	 ("rhslist", ["rhslist", toks.index("OR"), "rhs"], "rhslist_OR_rhs"),
	 ("rhs", ["rhsidlist"], "rhs_idlist"),
	 ("rhs", ["rhsidlist", toks.index("LPAREN"), toks.index("ID"), toks.index("RPAREN")], "rhs_idlist_func"),
	 ("rhsidlist", ["idlist"]),
         ("rhsidlist", [], "rhseps"),
	 ("idlist", ["idlist", toks.index("ID")], "idl_idlistID"),
	 ("idlist", [toks.index("ID")], "idlistID")])
#    print string.join(map(lambda x: str(x), prods), "\n")
    g = Grammar(prods, toks, 1)

#    g.extrasources = "import PyLR.Parsers"
    # produce the parser
    g.writefile("./Parsers/GrammarParser.py", "GrammarParser", "PyLR.Lexers.GrammarLex()")

def _test():
    # first a non-productive Grammar
    try:
        Grammar([Production("S", ["S"])], ["EOF"])
        assert 0, "Bummer!"
    except ParseError: pass
    # now a simple Grammar
    import Lexers
    toks = Lexers.MathLex().getTokenList()

    prods = map(_makeprod,
        [("expression", ["expression",toks.index("PLUS"),"term"], "addfunc"),
         ("expression", ["term"]),
         ("term", ["term", toks.index("TIMES"),"factor"], "timesfunc"),
         ("term", ["factor"]),
         ("factor", [toks.index("LPAR"), "expression", toks.index("RPAR")], "parenfunc"),
	 ("factor", [toks.index("INT")])])
    g = Grammar(prods, toks, 1)
    g.writefile("Parsers/MathParser.py", "MathParser", "PyLR.Lexers.MathLex()")

if __name__=='__main__':
#    _bootstrap()
    _test()

