# -*- coding: iso-8859-1 -*-
"""
This file is part of the pydns project.
Homepage: http://pydns.sourceforge.net

This code is covered by the standard Python License.

CLASS values (section 3.2.4)
"""


IN = 1          # the Internet
CS = 2          # the CSNET class (Obsolete - used only for examples in
                # some obsolete RFCs)
CH = 3          # the CHAOS class. When someone shows me python running on
                # a Symbolics Lisp machine, I'll look at implementing this.
HS = 4          # Hesiod [Dyer 87]

# QCLASS values (section 3.2.5)

ANY = 255       # any class


# Construct reverse mapping dictionary

_classmap = {}
for _name in dir():
    if not _name.startswith('_'):
        _classmap[eval(_name)] = _name

def classstr (klass):
    """return string representation of DNS class"""
    return _classmap.get(klass, repr(klass))

