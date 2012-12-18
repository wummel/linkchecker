# -*- coding: iso-8859-1 -*-
#
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# file created 2011-04-15


# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# This is a simple replacement for the standard Python exception handler (sys.excepthook).
# In addition to what the standard handler does, it also prints all referenced variables
# (no matter if local, global or builtin) of the code line of each stack frame.
# See below for some examples and some example output.

# https://github.com/albertz/py_better_exchook

from __future__ import print_function
import sys
import os

def parse_py_statement(line):
	state = 0
	curtoken = ""
	spaces = " \t\n"
	ops = ".,;:+-*/%&=|(){}[]^<>"
	i = 0
	def _escape_char(c):
		if c == "n": return "\n"
		elif c == "t": return "\t"
		else: return c
	while i < len(line):
		c = line[i]
		i += 1
		if state == 0:
			if c in spaces: pass
			elif c in ops: yield ("op", c)
			elif c == "#": state = 6
			elif c == "\"": state = 1
			elif c == "'": state = 2
			else:
				curtoken = c
				state = 3
		elif state == 1: # string via "
			if c == "\\": state = 4
			elif c == "\"":
				yield ("str", curtoken)
				curtoken = ""
				state = 0
			else: curtoken += c
		elif state == 2: # string via '
			if c == "\\": state = 5
			elif c == "'":
				yield ("str", curtoken)
				curtoken = ""
				state = 0
			else: curtoken += c
		elif state == 3: # identifier
			if c in spaces + ops + "#\"'":
				yield ("id", curtoken)
				curtoken = ""
				state = 0
				i -= 1
			else: curtoken += c
		elif state == 4: # escape in "
			curtoken += _escape_char(c)
			state = 1
		elif state == 5: # escape in '
			curtoken += _escape_char(c)
			state = 2
		elif state == 6: # comment
			curtoken += c
	if state == 3: yield ("id", curtoken)
	elif state == 6: yield ("comment", curtoken)


import keyword
pykeywords = set(keyword.kwlist)

def grep_full_py_identifiers(tokens):
	global pykeywords
	tokens = list(tokens)
	i = 0
	while i < len(tokens):
		tokentype, token = tokens[i]
		i += 1
		if tokentype != "id": continue
		while i+1 < len(tokens) and tokens[i] == ("op", ".") and tokens[i+1][0] == "id":
			token += "." + tokens[i+1][1]
			i += 2
		if token == "": continue
		if token in pykeywords: continue
		if token[0] in ".0123456789": continue
		yield token

def set_linecache(filename, source):
	import linecache
	linecache.cache[filename] = None, None, [line+'\n' for line in source.splitlines()], filename

def output(s, out=sys.stdout): print(s, file=out)

def output_limit():
	return 300

def pp_extra_info(obj, depthlimit = 3):
	s = []
	if hasattr(obj, "__len__"):
		try:
			if type(obj) in (str,unicode,list,tuple,dict) and len(obj) <= 5:
				pass # don't print len in this case
			else:
				s += ["len = " + str(obj.__len__())]
		except: pass
	if depthlimit > 0 and hasattr(obj, "__getitem__"):
		try:
			if type(obj) in (str,unicode):
				pass # doesn't make sense to get subitems here
			else:
				subobj = obj.__getitem__(0)
				extra_info = pp_extra_info(subobj, depthlimit - 1)
				if extra_info != "":
					s += ["_[0]: {" + extra_info + "}"]
		except: pass
	return ", ".join(s)
	
def pretty_print(obj):
	s = repr(obj)
	limit = output_limit()
	if len(s) > limit:
		s = s[:limit - 3] + "..."
	extra_info = pp_extra_info(obj)
	if extra_info != "": s += ", " + extra_info
	return s

def fallback_findfile(filename):
	mods = [ m for m in sys.modules.values() if m and hasattr(m, "__file__") and filename in m.__file__ ]
	if len(mods) == 0: return None
	altfn = mods[0].__file__
	if altfn[-4:-1] == ".py": altfn = altfn[:-1] # *.pyc or whatever
	return altfn

def better_exchook(etype, value, tb, out=sys.stdout):
	output('Traceback (most recent call last):', out=out)
	allLocals,allGlobals = {},{}
	try:
		import linecache
		limit = None
		if hasattr(sys, 'tracebacklimit'):
			limit = sys.tracebacklimit
		n = 0
		_tb = tb
		def _resolveIdentifier(namespace, id):
			obj = namespace[id[0]]
			for part in id[1:]:
				obj = getattr(obj, part)
			return obj
		def _trySet(old, prefix, func):
			if old is not None: return old
			try: return prefix + func()
			except KeyError: return old
			except Exception as e:
				return prefix + "!" + e.__class__.__name__ + ": " + str(e)
		while _tb is not None and (limit is None or n < limit):
			f = _tb.tb_frame
			allLocals.update(f.f_locals)
			allGlobals.update(f.f_globals)
			lineno = _tb.tb_lineno
			co = f.f_code
			filename = co.co_filename
			name = co.co_name
			output('  File "%s", line %d, in %s' % (filename,lineno,name), out=out)
			if not os.path.isfile(filename):
				altfn = fallback_findfile(filename)
				if altfn:
					output("    -- couldn't find file, trying this instead: " + altfn, out=out)
					filename = altfn
			linecache.checkcache(filename)
			line = linecache.getline(filename, lineno, f.f_globals)
			if line:
				line = line.strip()
				output('    line: ' + line, out=out)
				output('    locals:', out=out)
				alreadyPrintedLocals = set()
				for tokenstr in grep_full_py_identifiers(parse_py_statement(line)):
					splittedtoken = tuple(tokenstr.split("."))
					for token in map(lambda i: splittedtoken[0:i], range(1, len(splittedtoken) + 1)):
						if token in alreadyPrintedLocals: continue
						tokenvalue = None
						tokenvalue = _trySet(tokenvalue, "<local> ", lambda: pretty_print(_resolveIdentifier(f.f_locals, token)))
						tokenvalue = _trySet(tokenvalue, "<global> ", lambda: pretty_print(_resolveIdentifier(f.f_globals, token)))
						tokenvalue = _trySet(tokenvalue, "<builtin> ", lambda: pretty_print(_resolveIdentifier(f.f_builtins, token)))
						tokenvalue = tokenvalue or "<not found>"
						output('      ' + ".".join(token) + " = " + tokenvalue, out=out)
						alreadyPrintedLocals.add(token)
				if len(alreadyPrintedLocals) == 0: output("       no locals", out=out)
			else:
				output('    -- code not available --', out=out)
			_tb = _tb.tb_next
			n += 1

	except Exception:
		output("ERROR: cannot get more detailed exception info because:", out=out)
		import traceback
		for l in traceback.format_exc().split("\n"): output("   " + l, out=out)
		output("simple traceback:", out=out)
		traceback.print_tb(tb, None, out)

	import types
	def _some_str(value):
		try: return str(value)
		except: return '<unprintable %s object>' % type(value).__name__
	def _format_final_exc_line(etype, value):
		valuestr = _some_str(value)
		if value is None or not valuestr:
			line = "%s" % etype
		else:
			line = "%s: %s" % (etype, valuestr)
		return line
	if (isinstance(etype, BaseException) or
		(hasattr(types, "InstanceType") and isinstance(etype, types.InstanceType)) or
		etype is None or type(etype) is str):
		output(_format_final_exc_line(etype, value), out=out)
	else:
		output(_format_final_exc_line(etype.__name__, value), out=out)

def install():
	sys.excepthook = better_exchook
