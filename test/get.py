#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
"""print contents of an url"""

import httplib, urlparse, sys

def main (url):
    parts = urlparse.urlsplit(url)
    host = parts[1]
    path = urlparse.urlunsplit(('', '', parts[2], parts[3], parts[4]))
    h = httplib.HTTPConnection(host)
    h.set_debuglevel(1)
    h.connect()
    h.putrequest("GET", path, skip_host=True)
    h.putheader("Host", host)
    h.putheader("Accept-Encoding", "gzip;q=1.0, deflate;q=0.9, identity;q=0.5")
    h.endheaders()
    req = h.getresponse()
    print req.read()


if __name__=='__main__':
    main(sys.argv[1])
