# -*- coding: iso-8859-1 -*-
"""
 This file is part of the pydns project.
 Homepage: http://pydns.sourceforge.net

 This code is covered by the standard Python License.

 Status values in message header
"""

NOERROR   = 0 #   No Error                           [RFC 1035]
FORMERR   = 1 #   Format Error                       [RFC 1035]
SERVFAIL  = 2 #   Server Failure                     [RFC 1035]
NXDOMAIN  = 3 #   Non-Existent Domain                [RFC 1035]
NOTIMP    = 4 #   Not Implemented                    [RFC 1035]
REFUSED   = 5 #   Query Refused                      [RFC 1035]
YXDOMAIN  = 6 #   Name Exists when it should not     [RFC 2136]
YXRRSET   = 7 #   RR Set Exists when it should not   [RFC 2136]
NXRRSET   = 8 #   RR Set that should exist does not  [RFC 2136]
NOTAUTH   = 9 #   Server Not Authoritative for zone  [RFC 2136]
NOTZONE   = 10 #  Name not contained in zone         [RFC 2136]
BADVERS   = 16 #  Bad OPT Version                    [RFC 2671]
BADSIG    = 16 #  TSIG Signature Failure             [RFC 2845]
BADKEY    = 17 #  Key not recognized                 [RFC 2845]
BADTIME   = 18 #  Signature out of time window       [RFC 2845]
BADMODE   = 19 #  Bad TKEY Mode                      [RFC 2930]
BADNAME   = 20 #  Duplicate key name                 [RFC 2930]
BADALG    = 21 #  Algorithm not supported            [RFC 2930]

# Construct reverse mapping dictionary

_statusmap = {}
for _name in dir():
    if not _name.startswith('_'):
        _statusmap[eval(_name)] = _name

def statusstr (status):
    """return string representation of DNS status"""
    return _statusmap.get(status, repr(status))

