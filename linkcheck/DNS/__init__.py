# __init__.py for DNS class.

class Error (Exception):
    def __str__ (self):
        return 'DNS API error'

import Type,Opcode,Status,Class
from Base import *
from Lib import *
from lazy import *
Request = DnsRequest
Result = DnsResult

