# -*- coding: iso-8859-1 -*-
"""
 This file is part of the pydns project.
 Homepage: http://pydns.sourceforge.net

 This code is covered by the standard Python License.

 Opcode values in message header. RFC 1035, 1996, 2136.
"""



QUERY = 0
IQUERY = 1
STATUS = 2
NOTIFY = 4
UPDATE = 5

# Construct reverse mapping dictionary

_opcodemap = {}
for _name in dir():
    if not _name.startswith('_'):
        _opcodemap[eval(_name)] = _name

def opcodestr (opcode):
    """return string representation of DNS opcode"""
    return _opcodemap.get(opcode, repr(opcode))

