# Status values in message header

NOERROR       = 0
FORMERR       = 1
SERVFAIL      = 2
NXDOMAIN      = 3
NOTIMP        = 4
REFUSED       = 5

# Construct reverse mapping dictionary

_names = dir()
statusmap = {}
for _name in _names:
	if _name[0] != '_': statusmap[eval(_name)] = _name

def statusstr(status):
	if statusmap.has_key(status): return statusmap[status]
	else: return `status`
