# -*- coding: iso-8859-1 -*-
#
# This file is part of the pydns project.
# Homepage: http://pydns.sourceforge.net
#
# This code is covered by the standard Python License.
#
"""routines for lazy people."""

import bk.net.dns.Base

def revlookup (name, config):
    "convenience routine for doing a reverse lookup of an address"
    a = name.split('.')
    a.reverse()
    b = '.'.join(a)+'.in-addr.arpa'
    # this will only return one of any records returned.
    return Base.DnsRequest(b, config, qtype='ptr').req().answers[0]['data']

def mxlookup (name, config):
    """
    convenience routine for doing an MX lookup of a name. returns a
    sorted list of (preference, mail exchanger) records
    """
    a = Base.DnsRequest(name, config, qtype='mx').req().answers
    l = map(lambda x:x['data'], a)
    l.sort()
    return l
