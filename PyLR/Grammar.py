__version__ = "$Id$"

import time,string,types,parsertemplate

class PyLRParseError(ParseError):
    pass

class Production:
    """Production -- a Grammar is really just a list of productions.
    The expected structure is a symbol for the LHS and a list of
    symbols or symbols for the RHS."""
    def __init__(self, LHS, RHS, funcname="unspecified"):
	self.LHS = LHS
	self.RHS = RHS
	self.funcname = funcname
	self.func = None # will be assigned dynamically
        self.toklist = None

    def setfunc(self, func):
        """.setfunc(<callable>)  --used for the dynamic production
        of a parseengine directly from Grammar.mkengine(), instead of tables
        saved to a file."""
	self.func = func
	
    def setfuncname(self, name):
        """.setfuncname("") -- used by Grammar.writefile to produce
        prodinfo table that.  .setfunc associates a function value
        with the production for runtime, on the fly productions
        of parsing engine from Grammar."""
	self.funcname = name

    def __len__(self):
	return len(self.RHS)

    def __repr__(self):
        return self.getrep()

    def getrep(self, toklist=None):
	s = self.LHS+":"
        for t in self.RHS:
            if type(t)==types.IntType and toklist:
                s = s+" "+toklist[t]
            else:
                s = s+" "+str(t)
        if self.funcname: s = s+" ("+self.funcname+")"
        return s

    def items(self):
	return range(len(self.RHS) + 1)


class LR1Grammar:
    """Provides methods for producing the actiontable, the gototable, and the
    prodinfo table.  Using these functions, it can produce a python source
    code file with these tables or a parsing engine.
    Note that we assume the first production (productions[0]) to be the start
    symbol."""

    EPS = "<EPS>"
    EOF = "<EOF>"
    DummyLA = -1

    def __init__(self, productions, tokens=[], verbose=0):
	self.verbose = verbose
	self.productions = productions
        self.tokens = tokens
	self.nonterminals = []
        for p in self.productions:
            if p.LHS not in self.nonterminals:
                self.nonterminals.append(p.LHS)
        if self.verbose:
            print "Nonterminals:", self.nonterminals
	self.terminals = []
        for p in self.productions:
            for s in p.RHS:
                if not (s in self.terminals or s in self.nonterminals):
                    self.terminals.append(s)
        self.terminals.sort()
        if self.verbose:
            print "Terminals:", self.terminals
        # reduce the grammar
        self._reduceGrammar()
        # build map with productions who have the same LHS
	self.lhsprods = {}
	for lhs in self.nonterminals:
	    self.lhsprods[lhs] = filter(lambda x,l=lhs: x.LHS==l, self.productions)
        # immediate epsilon productions
	pi = 1
	self.epslhs = {}
	for p in self.productions:
	    if p.RHS == []:
		self.epslhs[p.LHS] = pi
	    pi = pi + 1
        # derived epsilon productions
	self.lhsdereps = self._mklhsdereps()
        # the FIRST function for the LR(1) grammar, implemented as a map
	self.firstmap = self._mkfirstmap()

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
        # rest_nt[p] == the number of nonterminals in p.RHS which are not yet
        # marked as productive
        # if rest_nt[p]==0 then p is productive
        rest_nt = {}
        # if we find a productive nonterminal A, we have to inspect all
        # other nonterminals with A. this is the reason we add all found
        # productive nts to this list
        workedon_nts = []
        # mark terminals as productive (even epsilon-prductions)
        for p in self.productions:
            rest_nt[p]= len(filter(lambda x, s=self: x in s.nonterminals, p.RHS))
            if rest_nt[p]==0:
                productive_nts[p] = 1
                workedon_nts.append(p)
        # work on the productive list
        while len(workedon_nts):
            x = workedon_nts[0]
            # search for production p with x in p.RHS
            for p in filter(lambda p, _x=x: _x in p.RHS, self.productions):
                rest_nt[p] = rest_nt[p] - 1
                if not p.LHS in productive_nts:
                    productive_nts.append(p.LHS)
                    workedon_nts.append(p.LHS)
            workedon_nts.remove(x)
        if not self.productions[0].LHS in productive_nts:
            raise PyLRParseError, "start symbol of grammar is not productive"

        # reachable nonterminals
        reachable_nts = self.productions[0]
        added=1
        while added:
            added = 0
            for p in self.productions:
                for r in p.RHS:
                    if p.LHS in reachable_nts and (r in self.nonterminals and
		    r not in reachable_nts):
                        reachable_nts.append(r)
                        added = 1

        # reduce the grammar
        self.productions = filter(lambda p,
                  pnt=productive_nts,
                  rnt=reachable_nts: p.LHS in pnt or p.LHS in rnt,
                  self.productions)

    def __repr__(self):
        """I like functional programming :)"""
	return string.join(map(lambda x,s=self: x.getrep(s.tokens),
	                       self.productions),";\n")+";"

    def _mklhsdereps(self):
	"""determines the nonterminals that derive nothing (epsilon)"""
	pi = 1                  
	res = {}
	for p in self.productions:
	    if p.RHS == []:
		res[p.LHS] = pi
	    pi = pi + 1
	workingnonterms = []
	for nt in self.nonterminals:
	    if not res.has_key(nt):
		workingnonterms.append(nt)
	while 1:
	    toremove = []
	    for nt in workingnonterms:
		if not res.has_key(nt):
		    for p in self.lhsprods[nt]:
			if len(p.RHS) == 1 and res.has_key(p.RHS[0]):
			    res[p.LHS] = res[p.RHS[0]]
			    toremove.append(nt)
			    break
	    if not toremove:
		break
	    for r in toremove:
		workingnonterms.remove(r)
	return res


    def _mkfirstmap(self):
	"""return a dictionary keyed by symbol whose values are the set
	of terminals that can precede that symbol
	"""
	res = {}
	for sym in self.terminals+[Grammar.EPS, Grammar.EOF, Grammar.DummyLA]:
	    res[sym] = {sym: 1}
        added=1
	while added:
	    added = 0
	    for nt in self.nonterminals:
		firsts = res.get(nt, {})
		for p in self.lhsprods[nt]:
		    if not p.RHS:
			if not firsts.has_key(Grammar.EPS):
			    added = firsts[Grammar.EPS] = 1
		    for i in range(len(p.RHS)):
			f = res.get(p.RHS[i], {})
			for t in f.keys():
			    if not firsts.has_key(t):
				added = firsts[t] = 1
			if not self.lhsdereps.has_key(p.RHS[i]):
			    break
		res[nt] = firsts
	for s in res.keys():
	    res[s] = res[s].keys()
	return res


    # these function are used as the grammar produces the tables (or writes
    # them to a file)
    def firstofstring(self, gs_list):
	tmpres = {}
	allhaveeps = 1
	for x in range(len(gs_list)):
	    tmp = self.firstmap[gs_list[x]]
	    for s in tmp:
		tmpres[s] = 1
	    if Grammar.EPS in tmp:
		del tmpres[Grammar.EPS]
	    else:
		allhaveeps = 0
		break
	if allhaveeps:
	    tmpres[Grammar.EPS] = 1
	return tmpres.keys()



    def augment(self):
	"""this function adds a production S' -> S to the grammar where S was
	the start symbol.
	"""
	lhss = map(lambda x: x.LHS, self.productions)
	newsym = self.productions[0].LHS
	while 1:
	    newsym = newsym + "'"
	    if newsym not in lhss:
		break
	self.productions.insert(0, Production(newsym, 
					      [self.productions[0].LHS]))


    # follow is not used yet, but probably will be in determining error reporting/recovery
    def follow(self):
	eof = Grammar.EOF
	follow = {}
	startsym = self.productions[0].LHS
	follow[startsym] = [eof]
	nts = self.nonterminals
	for p in self.productions:
	    cutoff = range(len(p.RHS))
	    cutoff.reverse()
	    for c in cutoff[:-1]:  # all but the first of the RHS elements
		f = self.firstmap[p.RHS[c]]
		if Grammar.EPS in f:
		    f.remove(Grammar.EPS)
		if follow.has_key(p.RHS[c - 1]):
		    if p.RHS[c -1] in nts:
			follow[p.RHS[c -1]] = follow[p.RHS[c - 1]] + f[:]
		else:
		    if p.RHS[c -1] in nts:
			follow[p.RHS[c - 1]] = f[:]
 	for p in self.productions:
	    if not p.RHS: continue
 	    cutoff = range(len(p.RHS))
 	    cutoff.reverse()
	    if p.RHS[-1] in nts:
		if follow.has_key(p.LHS):
		    add = follow[p.LHS]
		else:
		    add = []

		if follow.has_key(p.RHS[-1]):
		    follow[p.RHS[-1]] = follow[p.RHS[-1]] + add
		else:
		    follow[p.RHS[-1]] = add
 	    for c in cutoff[:-1]:
 		f = self.firstmap[p.RHS[c]]
 		if Grammar.EPS in f:
 		    if follow.has_key(p.LHS):
 			add = follow[p.LHS]
 		    else:
 			add = []
 		    if follow.has_key(p.RHS[c-1]):
 			follow[p.RHS[c-1]] = follow[p.RHS[c-1]] + add
 		    elif add:
 			follow[p.RHS[c - 1]] = add
	for k in follow.keys():
	    d = {}
	    for i in follow[k]:
		d[i] = 1
	    follow[k] = d.keys()
	return follow

    def closure(self, items):
	res = items[:]
	todo = items[:]
        more = 1
	while more:
	    more = []
	    for (prodind, rhsind), term in todo:
		if rhsind >= len(self.productions[prodind].RHS):
		    continue
		for p in self.lhsprods.get(self.productions[prodind].RHS[rhsind], []):
		    try:
			newpart = self.productions[prodind].RHS[rhsind + 1]
		    except IndexError:
			newpart = Grammar.EPS
		    stringofsyms = [newpart, term]
		    for t in self.firstofstring(stringofsyms):
			if ((self.productions.index(p), 0), t) not in res:
			    more.append(((self.productions.index(p), 0), t))
		    if term == Grammar.EOF and newpart == Grammar.EPS:
			if ((self.productions.index(p), 0), Grammar.EOF) not in res:
			    more.append(((self.productions.index(p), 0), Grammar.EOF))
	    if more:
		res = res + more
		todo = more
	return res

    def goto(self, items, sym):
	itemset = []
	for (prodind, rhsind), term in items:
	    try:
		if self.productions[prodind].RHS[rhsind] == sym and ((prodind, rhsind+1), term) not in itemset:
		    itemset.append( ((prodind, rhsind +1), term))
	    except IndexError:  
		pass
	return self.closure(itemset)

    def default_prodfunc(self):
	"""for mkengine, this will produce a default function for those
	unspecified
	"""
	return lambda *args: args[0]

    def prodinfotable(self):
	"""returns a list of three pieces of info for each production.
	The first is the lenght of the production, the second is the
	function(name) associated with the production and the third is
	is the index of the lhs in a list of nonterminals.
	"""
	res = []
	for p in self.productions:
	    lhsind = self.nonterminals.index(p.LHS)
	    func = p.func
	    if not func:
		func = self.default_prodfunc()
	    plen = len(p.RHS)
	    if p.RHS == [Grammar.EPS]:
		plen = 0
	    res.append((plen, func, lhsind))
	return res


class LALRGrammar(LR1Grammar):
    def __init__(self, prods, toks=[]):
	Grammar.__init__(self, prods, toks)
	self.LALRitems = []
        #
	# this is to help mak epsilon productions work with kernel items
	# and to compute goto transitions from kernel
	print "computing ntfirsts..."
	self.ntfirstmap = self._mkntfirstmap()
        #
	# this is to help make shifts work with only kernel items
	print "computing tfirsts..."
	self.tfirstmap = self._mktfirstmap()
	#
	# another thing to help epsilon productions
	print "computing follows..."
	self.followmap = self.follow()

    def _mkntfirstmap(self):
	"""computes all nonterms A, first of (strings n) such that some
	nonterminal B derives [A, n] in zero or more steps of (rightmost)
	derivation. used to help make epsilon productions quickly calculable.
	(B may == A)
	"""
	res = {}
	for p in self.productions:
	    if p.RHS and p.RHS[0] in self.nonterminals:
		fos = self.firstofstring(p.RHS[1:])
		fos.sort()
		if not res.has_key(p.LHS):
		    res[p.LHS] = {}
		if not res[p.LHS].has_key(p.RHS[0]):
		    res[p.LHS][p.RHS[0]] = []
		for i in fos:
		    if i not in res[p.LHS].get(p.RHS[0], []):
			res[p.LHS][p.RHS[0]] = fos
		
	while 1:
	    foundmore = 0
	    reskeys = res.keys()
	    for nt in reskeys:
		rhsdict = res[nt]
		for rnt in rhsdict.keys():
		    if rnt in reskeys:
			d = res[rnt]
			for k in d.keys():
			    if not res[nt].has_key(k):
				fos = self.firstofstring(d[k]+ res[nt][rnt]) 
				foundmore = 1
 				fos.sort()
 				res[nt][k] = fos
 			    else:
 				fos = self.firstofstring(d[k] + res[nt][rnt])
 				fos.sort()
 				if fos != res[nt][k]:  # then res[nt][k] is contained in fos
 				    foundmore = 1
 				    res[nt][k] = fos
	    if not foundmore:
		break
	#
	# this part accounts for the fact that a nonterminal will
	# produce exactly itself in zero steps
	#
	for p in self.productions:
	    if res.has_key(p.LHS):
                res[p.LHS][p.LHS] = [Grammar.EPS]
	    else:
		res[p.LHS] = {p.LHS: [Grammar.EPS]}
	return res
			    
    def newmkntfirstmap(self):
	"""computes all nonterms A, first of (strings n) such that some
	nonterminal B derives [A, n] in zero or more steps of (rightmost)
	derivation. used to help make epsilon productions quickly calculable.
	(B may == A)
	"""
	res = {}
	pi = 0
	for p in self.productions:
	    if p.RHS and p.RHS[0] in self.nonterminals:
		if not res.has_key(p.LHS):
		    res[p.LHS] = {}
		if not res[p.LHS].has_key(p.RHS[0]):
		    res[p.LHS][p.RHS[0]] = 1
	while 1:
	    foundmore = 0
	    reskeys = res.keys()
	    for nt in reskeys:
		rhsdict = res[nt]
		for rnt in rhsdict.keys():
		    if rnt in reskeys:
			d = res[rnt]
			for k in d.keys():
			    if not res[nt].has_key(k):
				foundmore = 1
 				res[nt][k] = 1
	    if not foundmore:
		break
	#
	# this part accounts for the fact that a nonterminal will
	# produce exactly itself in zero steps
	#
	for p in self.productions:
	    if res.has_key(p.LHS):
                res[p.LHS][p.LHS] = 1
	    else:
		res[p.LHS] = {p.LHS: 1}
	return res
	

	
    def _mktfirstmap(self):
	"""for each nonterminal C, compute the set of all terminals a, such
	that C derives ax in zero or more steps of (rightmost) derivation
	where the last derivation is not an epsilon (empty) production.
	
	assumes .mkfirstntmap() has been run and has already produced
	self.ntfirstmap
	"""
	res = {}
	for p in self.productions:
	    if not res.has_key(p.LHS):
		res[p.LHS] = []
	    if p.RHS and p.RHS[0] in self.terminals:
		res[p.LHS].append(p.RHS[0])
	while 1:
	    foundmore = 0
	    reskeys = res.keys()
	    for nt in self.ntfirstmap.keys():
		arrows = self.ntfirstmap[nt]
		for k in arrows.keys():
		    for t in res[k]:
			if t not in res[nt]:
			    foundmore = 1
			    res[nt].append(t)
	    if not foundmore:
		break
	return res

    def goto(self, itemset, sym):
	res = []
	for (pi, ri) in itemset:
	    if ri == len(self.productions[pi].RHS):
		continue
	    s = self.productions[pi].RHS[ri]
	    if s == sym:
		res.append((pi, ri+1))
            d = self.ntfirstmap.get(s, {})
	    for k in d.keys():
		for p in self.lhsprods[k]:
		    if p.RHS and p.RHS[0] == sym:
			i = self.productions.index(p)
			if (i, 1) not in res: res.append((i, 1))
	res.sort()
	return res

    def lookaheads(self, itemset):
	setsofitems = kernels = self.kernelitems
	spontaneous = []
	propagates = {}
	gotomap = {}
	for (kpi, kri) in itemset:
	    C = self.closure([((kpi, kri), Grammar.DummyLA)])
	    for (cpi, cri), t in C:
		if (cri) == len(self.productions[cpi].RHS):
		    continue
		s = self.productions[cpi].RHS[cri]
		if gotomap.has_key(s):
		    newstate = gotomap[s]
		else:
		    newstate = setsofitems.index(self.goto(itemset, s))
		    gotomap[s] = newstate
		if t != Grammar.DummyLA:
		    spontaneous.append((newstate, (cpi, cri+1), t))
		else:
 		    if propagates.has_key((kpi, kri)):
			propagates[(kpi, kri)].append((newstate, (cpi, cri+1)))
		    else:
			propagates[(kpi, kri)]=[(newstate, (cpi, cri+1))]
	return spontaneous, propagates

    def kernelsoflalr1items(self):
	res = [[(0, 0)]]
	todo = [[(0, 0)]]
	while 1:
	    newtodo = []
	    for items in todo:
		for s in self.terminals + self.nonterminals + [Grammar.EOF]:
		    g = self.goto(items, s)
		    if g and g not in res:
			newtodo.append(g)
	    if not newtodo:
		break
	    else:
		if self.verbose:
		    print "found %d more kernels" % (len(newtodo))
		res = res + newtodo
		todo = newtodo
	res.sort()
	return res

    def initLALR1items(self):
	self.kernelitems = kernels = self.kernelsoflalr1items()
	props = {}
	la_table = []
	for x in range(len(kernels)):
	    la_table.append([])
	    for y in range(len(kernels[x])):
		la_table[x].append([])
	la_table[0][0] = [Grammar.EOF]
	if self.verbose:
	    print "initLALR1items, kernels done, calculating propagations and spontaneous lookaheads"
	state_i = 0
	for itemset in kernels:
	    if self.verbose:
		print ".",
            sp, pr = self.lookaheads(itemset)
	    for ns, (pi, ri), t in sp:
                inner = kernels[ns].index((pi, ri))
		la_table[ns][inner].append(t)
	    props[state_i] = pr
	    state_i = state_i + 1
	return la_table, props

    def LALR1items(self):
	la_table, props = self.initLALR1items()
	if self.verbose:
	    print "done init LALR1items"
	soi = self.kernelitems
	while 1:
	    added_la = 0
	    state_i = 0
	    for state in la_table:
		ii = 0
		for propterms in state:
		    if not propterms:
			ii = ii + 1
			continue
		    item = soi[state_i][ii]
		    ii = ii + 1
		    try:
			proplist = props[state_i][item]
		    except KeyError:
			continue
		    for pstate, pitem in proplist:
			inner = soi[pstate].index(pitem)
			for pt in propterms:
			    if pt not in la_table[pstate][inner]:
				added_la = 1
				la_table[pstate][inner].append(pt)
		state_i = state_i + 1
	    if not added_la:
		break
	#
	# this section just reorganizes the above data
	# to the state it's used in later...
	# 
	if self.verbose:
	    print "done with lalr1items, reorganizing the data"
	res = []
	state_i = 0
	for state in soi:
	    item_i = 0
	    inner = []
	    for item in state:
 		for term in la_table[state_i][item_i]:
 		    if (item, term) not in inner:
 			inner.append((item, term))
		item_i = item_i + 1
	    inner.sort()
	    res.append(inner)
	    state_i = state_i + 1
	self.LALRitems = res
	return res

    def deriveN(self, nt1, nt2):
	"""
	assuming nt1 -> nt2 <some string>, what is <some string>? such that
	we know it as 1) a set of terminals and 2) whether it contains
	Grammar.EPS
	"""
	pass

    def actiontable(self):
	items = self.LALRitems
	res = []
	state_i = 0
	terms = self.terminals[:]
	terms.append(Grammar.EOF)
	errentry = ("", -1)
	for state in items:
	    list = [errentry] * len(terms)
	    res.append(list)
	    for (prodind, rhsind), term in state:
		if (rhsind ) == len(self.productions[prodind].RHS):
		    if prodind != 0:
			new = ("r", prodind)
			old = res[state_i][terms.index(term)]
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i, terms.index(term)), old, "->", new
			res[state_i][terms.index(term)] = new
		    else:
			new = ("a", -1)
			old = res[state_i][terms.index(term)]
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i, terms.index(term)), old, "->", new
			res[state_i][terms.index(term)] = new
		#
		# calculate reduction by epsilon productions 
		#
		elif self.productions[prodind].RHS[rhsind] in self.nonterminals:
		    nt = self.productions[prodind].RHS[rhsind]
		    ntfirst = self.firstmap[nt]
		    ntfirsts = self.ntfirstmap.get(nt, {})
		    for k in ntfirsts.keys():
			if self.epslhs.get(k, ""):
			    reduceterms = self.followmap[k]
#			    print `((prodind, rhsind), term)`, reduceterms
			    for r in reduceterms:
   				inner = terms.index(r)
   				old = res[state_i][inner]
   				new = ("r", self.epslhs[k])
  			        if old != errentry and old != new:
  				    print "Conflict[%d,%d]:" % (state_i, inner), old, "->", new
  				res[state_i][inner] = new
		    #
		    # calculate the shifts that occur but whose normal items aren't in the kernel
		    #
		    tfirsts = self.tfirstmap[nt]
		    for t in tfirsts:
			inner = terms.index(t)
			g = self.goto(self.kernelitems[state_i], t)
			old = res[state_i][inner]
			try:
			    news = self.kernelitems.index(g)
			except ValueError:
			    continue
			new = ("s", news)
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i, inner), old, "->", new			    
			res[state_i][inner] = new
		#
		# compute the rest of the shifts that occur 'normally' in the kernel
		#
		else:
		    t = self.productions[prodind].RHS[rhsind]
		    inner = self.terminals.index(t)
		    gt = self.goto(self.kernelitems[state_i], t)
		    if gt in self.kernelitems:
			news = self.kernelitems.index(gt)
			old = res[state_i][inner]
			new = ("s", news)
			if old != errentry and old != new:
			    print "Conflict[%d,%d]:" % (state_i, inner), old, "->", new			    
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
	    list = [err] * len(nonterms)
	    res.append(list)
	    nonterm_i = 0
	    for nt in nonterms:
		goto = self.goto(state, nt)
		if goto in items:
		    res[state_i][nonterm_i] = items.index(goto)
		nonterm_i = nonterm_i + 1
	    state_i = state_i + 1
	return res

    def mkengine(self, inbufchunksize=None, stackchunksize=None):
	"""dynamically will produde a parse engine, just an experiment,
	don't try to use it for anything real.
	"""
	self.augment()
	self.LALR1items()
	at = self.actiontable()
	gt = self.gototable()
	self.productions = self.productions[1:]  # unaugment
	pi = self.prodinfotable()
	if not inbufchunksize:
	    inbufchunksize = 50
	if not stackchunksize:
	    stackchunksize = 100
	e = PyLRengine.NewEngine(pi, at, gt, inbufchunksize, stackchunksize)
	return e

    def writefile(self, filename, parsername="MyParser", lexerinit = "PyLR.Lexer.Lexer()"):
	self.augment()
	print "About to start LALRitems at %d" % time.time()
	self.LALR1items()
	print "done building LALRitems at %d" % time.time()
	at = self.actiontable()
	print "done building actiontable at %d" % time.time()
	gt = self.gototable()
	print "done building gototable at %d" % time.time()
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
    # dang, how did Scott bootstrap the GrammarParser??
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
    print string.join(map(lambda x: str(x), prods), "\n")
    g = LALRGrammar(prods, toks)

#    g.extrasources = "import PyLR.Parsers"
    # produce the parser
    g.writefile("./Parsers/GrammarParser.py", "GrammarParser", "PyLR.Lexers.GrammarLex()")

if __name__=='__main__':
    _bootstrap()

