#!/opt/python/bin/python1.5

import DNS
# automatically load nameserver(s) from /etc/resolv.conf
# (works on unix - on others, YMMV)
DNS.ParseResolvConf()

r=DNS.Request(qtype='mx')
res = r.req('connect.com.au')
res.show()

r=DNS.Request(qtype='soa')
res = r.req('connect.com.au')
res.show()

print DNS.revlookup('192.189.54.17')

