#!/opt/python/bin/python1.5

import DNS
# automatically load nameserver(s) from /etc/resolv.conf
# (works on unix - on others, YMMV)
DNS.ParseResolvConf()

# web server reliability, the NT way. *snigger*
res = r.req('www.microsoft.com',qtype='A')
# res.answers is a list of dictionaries of answers
print len(res.answers),'different A records'
# each of these has an entry for 'data', which is the result.
print map(lambda x:x['data'], res.answers)
