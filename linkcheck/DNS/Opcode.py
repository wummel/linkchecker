# -*- coding: iso-8859-1 -*-
"""
 $Id$

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

_names = dir()
opcodemap = {}
for _name in _names:
    if _name[0] != '_': opcodemap[eval(_name)] = _name

def opcodestr(opcode):
    return opcodemap.get(opcode, repr(opcode))

#
# $Log$
# Revision 1.5  2003/12/20 11:28:15  calvin
# replace backticks with repr
#
# Revision 1.4  2003/07/04 14:23:22  calvin
# add coding line
#
# Revision 1.3  2002/11/26 23:27:43  calvin
# update to Python >= 2.2.1
#
# Revision 1.6  2002/04/23 10:51:43  anthonybaxter
# Added UPDATE, NOTIFY.
#
# Revision 1.5  2002/03/19 12:41:33  anthonybaxter
# tabnannied and reindented everything. 4 space indent, no tabs.
# yay.
#
# Revision 1.4  2002/03/19 12:26:13  anthonybaxter
# death to leading tabs.
#
# Revision 1.3  2001/08/09 09:08:55  anthonybaxter
# added identifying header to top of each file
#
# Revision 1.2  2001/07/19 06:57:07  anthony
# cvs keywords added
#
#
