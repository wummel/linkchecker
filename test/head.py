#!/usr/bin/python
"""print headers of an url"""

import httplib, urlparse, sys

def main (url):
    parts = urlparse.urlsplit(url)
    host = parts[1]
    path = urlparse.urlunsplit(('', '', parts[2], parts[3], parts[4]))
    h = httplib.HTTPConnection(host)
    h.connect()
    h.putrequest("HEAD", path, skip_host=1)
    h.putheader("Host", host)
    h.endheaders()
    req = h.getresponse()
    print req.msg


if __name__=='__main__':
    main(sys.argv[1])
