# garbage functions

    def _goto(self, items, sym):
        """Reference: [Aho,Seti,Ullmann: Compilerbau Teil 1, p. 282]
        """
	itemset = {}
	for prodind, rhsind, sym in items.keys():
            try:
                if self.productions[prodind].rhs[rhsind] == sym:
                    itemset[(prodind, rhsind+1, sym)] = 0
            except IndexError:
                pass
	return self._closure(itemset)

    def _genLR1Items(self):
        """Reference: [Aho,Seti,Ullmann: Compilerbau Teil 1, p. 283]
        This function is only for completeness (and not tested).
	We normally use LALR parsers instead of LR(1) parsers.
        Calculate the LR(1) items
        Notation: we have self.production[i] == A --> x0...x(m-1) · xm and
	symbol s. Then we construct a triple (i, m, s).
        An item set is represented by a dictionary
        self.LR1Items is a list of dictionaries, representing a set of sets
        """
        self.LR1Items = [self._closure({(0,0,0):0})]
        added=1
        while added:
            added=0
            for set in self.LR1Items:
                for X in self.terminals+self.nonterminals+[LR1Grammar.EPS]:
                    gotoset = self._goto(set, X)
                    if gotoset and gotoset not in self.LR1Items:
                        self.LR1Items.append(gotoset)
                        added=1

    def deriveN(self, nt1, nt2):
	"""
	assuming nt1 -> nt2 <some string>, what is <some string>? such that
	we know it as 1) a set of terminals and 2) whether it contains
	Grammar.EPS
	"""
	pass

    def _genNTFIRSTmap(self):
	"""computes all nonterms A, first of (strings n) such that some
	nonterminal B derives [A, n] in zero or more steps of (rightmost)
	derivation. used to help make epsilon productions quickly calculable.
	(B may == A)
	"""
	self.ntfirstmap = {}
	for p in self.productions:
	    if p.rhs and p.rhs[0] in self.nonterminals:
		fos = self.firstofstring(p.rhs[1:])
		fos.sort()
		if not self.ntfirstmap.has_key(p.lhs):
		    self.ntfirstmap[p.lhs] = {}
		if not self.ntfirstmap[p.lhs].has_key(p.rhs[0]):
		    self.ntfirstmap[p.lhs][p.rhs[0]] = []
		for i in fos:
		    if i not in self.ntfirstmap[p.lhs].get(p.rhs[0], []):
			self.ntfirstmap[p.lhs][p.rhs[0]] = fos

        foundmore=1
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
				fos = self.FIRST(d[k]+self.ntfirstmap[nt][rnt])
				foundmore = 1
 				fos.sort()
 				self.ntfirstmap[nt][k] = fos
 			    else:
 				fos = self.FIRST(d[k] + res[nt][rnt])
 				fos.sort()
 				if fos != self.ntfirstmap[nt][k]:  # then res[nt][k] is contained in fos
 				    foundmore = 1
 				    self.ntfirstmap[nt][k] = fos
	# this part accounts for the fact that a nonterminal will
	# produce exactly itself in zero steps
	for p in self.productions:
	    if self.ntfirstmap.has_key(p.lhs):
                self.ntfirstmap[p.lhs][p.lhs] = [Grammar.EPS]
	    else:
		self.ntfirstmap[p.lhs] = {p.lhs: [Grammar.EPS]}


